"""Stable local identity for one Seven installation."""
from __future__ import annotations

import json
import os
import re
import secrets
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


_NODE_ID = re.compile(r"^[a-f0-9]{32}$")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NodeIdentity:
    node_id: str
    created_at: str


def load_or_create_identity(data_dir: Path) -> NodeIdentity:
    """Load or atomically create a private, stable node identifier."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "mesh_identity.json"
    def load() -> NodeIdentity:
        payload = json.loads(path.read_text(encoding="utf-8"))
        identity = NodeIdentity(
            node_id=str(payload["node_id"]),
            created_at=str(payload["created_at"]),
        )
        if not _NODE_ID.fullmatch(identity.node_id):
            raise ValueError("invalid node_id")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return identity

    try:
        return load()
    except FileNotFoundError:
        pass
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Seven mesh identity file: {path}") from exc

    lock_path = path.with_name(f".{path.name}.lock")
    lock_fd: int | None = None
    deadline = time.monotonic() + 5.0
    while lock_fd is None:
        try:
            lock_fd = os.open(
                lock_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except (FileExistsError, PermissionError):
            try:
                return load()
            except FileNotFoundError:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError(f"timed out waiting for Seven mesh identity: {path}")
            time.sleep(0.02)

    # A caller that began before the first writer published the identity can
    # acquire the lock just after that writer releases it. Re-check while
    # holding the lock so a late contender never replaces the stable identity.
    try:
        existing = load()
    except FileNotFoundError:
        existing = None
    if existing is not None:
        os.close(lock_fd)
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass
        return existing

    identity = NodeIdentity(node_id=secrets.token_hex(16), created_at=_utcnow())
    raw = (
        json.dumps(asdict(identity), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )
    try:
        with os.fdopen(lock_fd, "w", encoding="utf-8") as lock_stream:
            lock_stream.write(str(os.getpid()))
            lock_stream.flush()
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass
    return identity
