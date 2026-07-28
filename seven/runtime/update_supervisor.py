"""External, transactional update supervisor for Seven.

This module is deliberately not registered as an LLM tool.  It is intended to
run in a separate supervisor process so the process being replaced never
updates itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence

from seven.runtime.process import run_tracked


_RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class CommandRunner(Protocol):
    def run(
        self, args: Sequence[str], *, cwd: Path | None = None, timeout: float = 600
    ) -> CommandResult: ...


class ProcessRunner:
    """Command runner with process-tree timeout cleanup and no shell."""

    def run(
        self, args: Sequence[str], *, cwd: Path | None = None, timeout: float = 600
    ) -> CommandResult:
        result = run_tracked(
            [str(arg) for arg in args],
            cwd=str(cwd) if cwd else None,
            timeout=timeout,
            shell=False,
        )
        return CommandResult(
            args=tuple(str(arg) for arg in args),
            returncode=int(result.returncode if result.returncode is not None else -1),
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )


class ServiceController(Protocol):
    """Host-specific service operations supplied by the deployment owner."""

    def restart(self, release: Path) -> CommandResult: ...

    def healthy(self, release: Path) -> CommandResult: ...


class CommandServiceController:
    """Service controller backed by explicit argv templates.

    ``{release}`` is replaced in individual arguments.  Commands never pass
    through a shell.
    """

    def __init__(
        self,
        runner: CommandRunner,
        restart_command: Sequence[str],
        health_command: Sequence[str],
        *,
        timeout: float = 120,
    ) -> None:
        if not restart_command or not health_command:
            raise ValueError("restart and health commands are required")
        self.runner = runner
        self.restart_command = tuple(restart_command)
        self.health_command = tuple(health_command)
        self.timeout = timeout

    @staticmethod
    def _render(command: Sequence[str], release: Path) -> tuple[str, ...]:
        return tuple(str(arg).replace("{release}", str(release)) for arg in command)

    def restart(self, release: Path) -> CommandResult:
        return self.runner.run(
            self._render(self.restart_command, release), timeout=self.timeout
        )

    def healthy(self, release: Path) -> CommandResult:
        return self.runner.run(
            self._render(self.health_command, release), timeout=self.timeout
        )


@dataclass(frozen=True)
class UpdateSpec:
    source: str
    ref: str = "main"
    release_id: str | None = None
    test_commands: tuple[tuple[str, ...], ...] = (
        (sys.executable, "-m", "pytest", "-q"),
    )
    candidate_health_command: tuple[str, ...] = (
        sys.executable,
        "-c",
        "import seven; print(seven.__version__)",
    )
    command_timeout: float = 900


@dataclass
class UpdateReport:
    transaction_id: str
    mode: str
    source: str
    ref: str
    release_id: str
    candidate: str
    previous_release: str | None
    started_at: str
    finished_at: str | None = None
    commit: str | None = None
    status: str = "planned"
    activated: bool = False
    rolled_back: bool = False
    steps: list[dict[str, object]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in {"planned", "validated", "activated"}


class UpdateSupervisor:
    """Build, verify, activate, and roll back immutable Seven releases."""

    def __init__(
        self,
        root: Path,
        *,
        runner: CommandRunner | None = None,
        service: ServiceController | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.releases = self.root / "releases"
        self.staging = self.root / ".staging"
        self.transactions = self.root / "transactions"
        self.backups = self.root / "backups"
        self.pointer = self.root / "current.json"
        self.runner = runner or ProcessRunner()
        self.service = service

    def plan(self, spec: UpdateSpec) -> UpdateReport:
        return self.run(spec, mode="plan")

    def dry_run(self, spec: UpdateSpec) -> UpdateReport:
        return self.run(spec, mode="dry-run")

    def apply(self, spec: UpdateSpec) -> UpdateReport:
        return self.run(spec, mode="apply")

    def run(self, spec: UpdateSpec, *, mode: str) -> UpdateReport:
        if mode not in {"plan", "dry-run", "apply"}:
            raise ValueError("mode must be plan, dry-run, or apply")
        release_id = spec.release_id or self._default_release_id(spec)
        if not _RELEASE_ID.fullmatch(release_id):
            raise ValueError("release_id contains unsafe characters")
        candidate = (self.releases / release_id).resolve()
        if self.releases.resolve() not in candidate.parents:
            raise ValueError("candidate path escapes releases directory")
        previous = self.read_pointer()
        transaction_id = uuid.uuid4().hex
        report = UpdateReport(
            transaction_id=transaction_id,
            mode=mode,
            source=spec.source,
            ref=spec.ref,
            release_id=release_id,
            candidate=str(candidate),
            previous_release=previous.get("release") if previous else None,
            started_at=_utc_now(),
        )
        report.steps.extend(
            [
                {"name": "isolated_checkout", "status": "planned"},
                {"name": "tests", "status": "planned"},
                {"name": "candidate_health", "status": "planned"},
                {"name": "atomic_activation", "status": "planned"},
                {"name": "service_restart", "status": "planned"},
                {"name": "post_activation_health", "status": "planned"},
                {"name": "automatic_rollback", "status": "armed"},
            ]
        )
        if mode == "plan":
            report.finished_at = _utc_now()
            return report
        if mode == "apply" and self.service is None:
            report.status = "failed"
            report.errors.append("apply requires an explicit ServiceController")
            report.finished_at = _utc_now()
            return report

        self._ensure_layout()
        stage = self.staging / f"{release_id}-{transaction_id}"
        promoted = False
        activated = False
        try:
            if candidate.exists():
                raise FileExistsError(f"release already exists: {candidate}")
            stage.mkdir(parents=True)
            clone = self._run_step(
                report,
                "isolated_checkout",
                ("git", "clone", "--no-local", "--no-hardlinks", spec.source, str(stage)),
                timeout=spec.command_timeout,
            )
            if not clone.ok:
                raise RuntimeError("isolated checkout failed")
            checkout = self._run_step(
                report,
                "checkout_ref",
                ("git", "checkout", "--detach", spec.ref),
                cwd=stage,
                timeout=spec.command_timeout,
            )
            if not checkout.ok:
                raise RuntimeError("ref checkout failed")
            revision = self._run_step(
                report, "resolve_commit", ("git", "rev-parse", "HEAD"), cwd=stage
            )
            if not revision.ok or not revision.stdout.strip():
                raise RuntimeError("could not resolve candidate commit")
            report.commit = revision.stdout.strip().splitlines()[0]

            for index, command in enumerate(spec.test_commands, start=1):
                outcome = self._run_step(
                    report,
                    f"tests_{index}",
                    command,
                    cwd=stage,
                    timeout=spec.command_timeout,
                )
                if not outcome.ok:
                    raise RuntimeError(f"test command {index} failed")
            health = self._run_step(
                report,
                "candidate_health",
                spec.candidate_health_command,
                cwd=stage,
                timeout=spec.command_timeout,
            )
            if not health.ok:
                raise RuntimeError("candidate health check failed")

            if mode == "dry-run":
                report.status = "validated"
                return report

            os.replace(stage, candidate)
            promoted = True
            self._backup_pointer(transaction_id)
            self._write_pointer(
                {
                    "format": 1,
                    "release": str(candidate),
                    "release_id": release_id,
                    "commit": report.commit,
                    "transaction_id": transaction_id,
                    "activated_at": _utc_now(),
                }
            )
            activated = True
            report.activated = True
            self._mark_step(report, "atomic_activation", "ok")

            restart = self.service.restart(candidate)  # type: ignore[union-attr]
            self._record_result(report, "service_restart", restart)
            if not restart.ok:
                raise RuntimeError("service restart failed")
            post_health = self.service.healthy(candidate)  # type: ignore[union-attr]
            self._record_result(report, "post_activation_health", post_health)
            if not post_health.ok:
                raise RuntimeError("post-activation health check failed")
            report.status = "activated"
            return report
        except Exception as exc:
            report.errors.append(str(exc))
            if activated:
                self._rollback(report, previous)
            report.status = "rolled_back" if report.rolled_back else "failed"
            return report
        finally:
            if stage.exists():
                self._remove_tree(stage, within=self.staging)
            if mode == "dry-run" and promoted and candidate.exists():
                self._remove_tree(candidate, within=self.releases)
            report.finished_at = _utc_now()
            if mode == "apply":
                self._write_transaction(report)

    def read_pointer(self) -> dict[str, object] | None:
        if not self.pointer.exists():
            return None
        value = json.loads(self.pointer.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("release"), str):
            raise ValueError(f"invalid activation pointer: {self.pointer}")
        return value

    def _rollback(
        self, report: UpdateReport, previous: dict[str, object] | None
    ) -> None:
        try:
            if previous:
                self._write_pointer(previous)
                old_release = Path(str(previous["release"])).resolve()
                restart = self.service.restart(old_release)  # type: ignore[union-attr]
                self._record_result(report, "rollback_restart", restart)
                healthy = self.service.healthy(old_release)  # type: ignore[union-attr]
                self._record_result(report, "rollback_health", healthy)
                if not restart.ok or not healthy.ok:
                    report.errors.append("rollback service verification failed")
                    return
            else:
                self.pointer.unlink(missing_ok=True)
            report.rolled_back = True
            report.activated = False
            self._mark_step(report, "automatic_rollback", "ok")
        except Exception as exc:
            report.errors.append(f"rollback failed: {exc}")

    def _ensure_layout(self) -> None:
        for directory in (
            self.root,
            self.releases,
            self.staging,
            self.transactions,
            self.backups,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _remove_tree(path: Path, *, within: Path) -> None:
        """Remove one verified work tree, including read-only Git objects."""
        path = path.resolve()
        within = within.resolve()
        if within not in path.parents or path == within:
            raise ValueError(f"refusing to remove path outside work root: {path}")

        def make_writable_and_retry(function, target, _error_info) -> None:
            os.chmod(target, stat.S_IWRITE)
            function(target)

        shutil.rmtree(path, onerror=make_writable_and_retry)

    def _backup_pointer(self, transaction_id: str) -> None:
        backup = self.backups / f"{transaction_id}-current.json"
        payload = self.pointer.read_bytes() if self.pointer.exists() else b""
        backup.write_bytes(payload)

    def _write_pointer(self, value: dict[str, object]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.root / f".current-{uuid.uuid4().hex}.tmp"
        data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        temp.write_bytes(data)
        os.replace(temp, self.pointer)

    def _write_transaction(self, report: UpdateReport) -> None:
        self.transactions.mkdir(parents=True, exist_ok=True)
        target = self.transactions / f"{report.transaction_id}.json"
        temp = target.with_suffix(".tmp")
        temp.write_text(
            json.dumps(asdict(report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, target)

    def _run_step(
        self,
        report: UpdateReport,
        name: str,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 600,
    ) -> CommandResult:
        result = self.runner.run(args, cwd=cwd, timeout=timeout)
        self._record_result(report, name, result)
        return result

    @staticmethod
    def _record_result(
        report: UpdateReport, name: str, result: CommandResult
    ) -> None:
        report.steps.append(
            {
                "name": name,
                "status": "ok" if result.ok else "failed",
                "args": list(result.args),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "stdout_sha256": hashlib.sha256(
                    result.stdout.encode("utf-8", errors="replace")
                ).hexdigest(),
                "stderr_sha256": hashlib.sha256(
                    result.stderr.encode("utf-8", errors="replace")
                ).hexdigest(),
            }
        )

    @staticmethod
    def _mark_step(report: UpdateReport, name: str, status: str) -> None:
        report.steps.append({"name": name, "status": status})

    @staticmethod
    def _default_release_id(spec: UpdateSpec) -> str:
        safe_ref = re.sub(r"[^A-Za-z0-9._-]", "-", spec.ref).strip(".-") or "ref"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{safe_ref}"[:128]


def resolve_active_release(root: Path) -> Path:
    """Resolve and validate the immutable release selected by the pointer."""
    supervisor = UpdateSupervisor(root)
    pointer = supervisor.read_pointer()
    if not pointer:
        raise FileNotFoundError("Seven has no active release pointer")
    release = Path(str(pointer["release"])).resolve()
    releases = supervisor.releases.resolve()
    if releases not in release.parents or not release.is_dir():
        raise ValueError("active release is missing or outside releases directory")
    return release
