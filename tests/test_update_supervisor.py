from __future__ import annotations

import json
import stat
from pathlib import Path

from seven.runtime.update_supervisor import (
    CommandResult,
    UpdateSpec,
    UpdateSupervisor,
    resolve_active_release,
)


class FakeRunner:
    def __init__(self, failures: set[str] | None = None) -> None:
        self.failures = failures or set()
        self.calls: list[tuple[tuple[str, ...], Path | None]] = []

    def run(self, args, *, cwd=None, timeout=600):
        args = tuple(str(value) for value in args)
        cwd = Path(cwd) if cwd else None
        self.calls.append((args, cwd))
        if args[:2] == ("git", "clone"):
            Path(args[-1]).mkdir(parents=True, exist_ok=True)
            (Path(args[-1]) / "candidate.txt").write_text("isolated", encoding="utf-8")
        key = args[0]
        failed = key in self.failures
        stdout = "abc123\n" if args[:3] == ("git", "rev-parse", "HEAD") else "ok\n"
        return CommandResult(args, 1 if failed else 0, stdout, "failed" if failed else "")


class FakeService:
    def __init__(self, *, restart_results=None, health_results=None) -> None:
        self.restart_results = list(restart_results or [True])
        self.health_results = list(health_results or [True])
        self.restarts: list[Path] = []
        self.health_checks: list[Path] = []

    @staticmethod
    def _result(name: str, ok: bool) -> CommandResult:
        return CommandResult((name,), 0 if ok else 1)

    def restart(self, release: Path) -> CommandResult:
        self.restarts.append(release)
        return self._result("restart", self.restart_results.pop(0))

    def healthy(self, release: Path) -> CommandResult:
        self.health_checks.append(release)
        return self._result("health", self.health_results.pop(0))


def spec(release_id: str) -> UpdateSpec:
    return UpdateSpec(
        source="C:/source/seven",
        ref="main",
        release_id=release_id,
        test_commands=(("tests",),),
        candidate_health_command=("candidate-health",),
    )


def test_plan_is_read_only(tmp_path):
    root = tmp_path / "supervisor"
    report = UpdateSupervisor(root, runner=FakeRunner()).plan(spec("v1"))
    assert report.ok
    assert report.status == "planned"
    assert not root.exists()


def test_dry_run_checks_candidate_without_activation(tmp_path):
    root = tmp_path / "supervisor"
    runner = FakeRunner()
    report = UpdateSupervisor(root, runner=runner).dry_run(spec("v1"))
    assert report.ok
    assert report.status == "validated"
    assert report.commit == "abc123"
    assert not (root / "current.json").exists()
    assert not (root / "releases" / "v1").exists()
    assert any(call[0][0] == "tests" for call in runner.calls)


def test_apply_activates_only_after_tests_and_health(tmp_path):
    root = tmp_path / "supervisor"
    service = FakeService()
    report = UpdateSupervisor(
        root, runner=FakeRunner(), service=service
    ).apply(spec("v1"))
    assert report.ok
    assert report.status == "activated"
    assert report.activated
    assert resolve_active_release(root) == (root / "releases" / "v1").resolve()
    pointer = json.loads((root / "current.json").read_text(encoding="utf-8"))
    assert pointer["commit"] == "abc123"
    assert service.restarts == [(root / "releases" / "v1").resolve()]
    assert list((root / "transactions").glob("*.json"))


def test_failed_candidate_never_changes_pointer(tmp_path):
    root = tmp_path / "supervisor"
    root.mkdir()
    old = root / "releases" / "old"
    old.mkdir(parents=True)
    old_pointer = {
        "format": 1,
        "release": str(old.resolve()),
        "release_id": "old",
        "commit": "oldsha",
    }
    (root / "current.json").write_text(json.dumps(old_pointer), encoding="utf-8")
    report = UpdateSupervisor(
        root,
        runner=FakeRunner({"tests"}),
        service=FakeService(),
    ).apply(spec("bad"))
    assert not report.ok
    assert report.status == "failed"
    assert json.loads((root / "current.json").read_text(encoding="utf-8")) == old_pointer
    assert not (root / "releases" / "bad").exists()


def test_failed_post_activation_health_rolls_back(tmp_path):
    root = tmp_path / "supervisor"
    old = root / "releases" / "old"
    old.mkdir(parents=True)
    old_pointer = {
        "format": 1,
        "release": str(old.resolve()),
        "release_id": "old",
        "commit": "oldsha",
    }
    root.mkdir(exist_ok=True)
    (root / "current.json").write_text(json.dumps(old_pointer), encoding="utf-8")
    service = FakeService(restart_results=[True, True], health_results=[False, True])
    report = UpdateSupervisor(
        root, runner=FakeRunner(), service=service
    ).apply(spec("bad-health"))
    assert not report.ok
    assert report.status == "rolled_back"
    assert report.rolled_back
    assert not report.activated
    assert json.loads((root / "current.json").read_text(encoding="utf-8")) == old_pointer
    assert service.restarts[-1] == old.resolve()
    assert service.health_checks[-1] == old.resolve()


def test_apply_requires_explicit_service_controller(tmp_path):
    report = UpdateSupervisor(
        tmp_path / "supervisor", runner=FakeRunner()
    ).apply(spec("v1"))
    assert not report.ok
    assert "ServiceController" in report.errors[0]
    assert not (tmp_path / "supervisor").exists()


def test_rejects_unsafe_release_id(tmp_path):
    supervisor = UpdateSupervisor(tmp_path / "supervisor", runner=FakeRunner())
    try:
        supervisor.plan(spec("../escape"))
    except ValueError as exc:
        assert "unsafe" in str(exc)
    else:
        raise AssertionError("unsafe release id accepted")


def test_cleanup_handles_read_only_git_objects(tmp_path):
    root = tmp_path / "supervisor"
    tree = root / ".staging" / "candidate"
    tree.mkdir(parents=True)
    read_only = tree / "pack.idx"
    read_only.write_text("pack", encoding="utf-8")
    read_only.chmod(stat.S_IREAD)
    UpdateSupervisor._remove_tree(tree, within=root / ".staging")
    assert not tree.exists()
