"""OpenSSH client tools with strict host-key verification and no password storage."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from seven.runtime.process import run_tracked

_TARGET = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validate(name: str, value: str) -> str:
    value = (value or "").strip()
    if not value or not _TARGET.fullmatch(value):
        raise ValueError(f"invalid {name}; use letters, numbers, dot, underscore or hyphen")
    return value


def _options(port: int, identity_file: str, known_hosts_file: str, timeout: int) -> list[str]:
    port = max(1, min(int(port), 65535))
    timeout = max(1, min(int(timeout), 600))
    args = [
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", "PasswordAuthentication=no",
        "-o", f"ConnectTimeout={min(timeout, 60)}",
        "-p", str(port),
    ]
    if identity_file:
        identity = Path(identity_file).expanduser().resolve()
        if not identity.is_file():
            raise ValueError(f"identity file not found: {identity}")
        args += ["-i", str(identity)]
    if known_hosts_file:
        known_hosts = Path(known_hosts_file).expanduser().resolve()
        if not known_hosts.is_file():
            raise ValueError(f"known-hosts file not found: {known_hosts}")
        args += ["-o", f"UserKnownHostsFile={known_hosts}"]
    return args


def ssh_status() -> str:
    return json.dumps({
        "ssh": shutil.which("ssh"),
        "scp": shutil.which("scp"),
        "authentication": "agent or identity file only",
        "strict_host_key_checking": True,
        "password_storage": False,
    }, indent=2)


def _result(completed, timeout: int) -> dict:
    return {
        "ok": completed.returncode == 0 and not completed.timed_out,
        "exit_code": completed.returncode,
        "timed_out": completed.timed_out,
        "terminated_pids": list(completed.terminated_pids),
        "stdout": completed.stdout[:50_000],
        "stderr": completed.stderr[:20_000],
        "output_truncated": len(completed.stdout) > 50_000 or len(completed.stderr) > 20_000,
        "timeout_seconds": timeout,
    }


def ssh_run(host: str, username: str, command: str, port: int = 22, identity_file: str = "", known_hosts_file: str = "", timeout: int = 60) -> str:
    executable = shutil.which("ssh")
    if not executable:
        return json.dumps({"ok": False, "state": "not_started", "error": "OpenSSH ssh client not found"}, indent=2)
    try:
        host, username = _validate("host", host), _validate("username", username)
        if not (command or "").strip():
            raise ValueError("command is required")
        timeout = max(1, min(int(timeout), 600))
        args = [executable, *_options(port, identity_file, known_hosts_file, timeout), f"{username}@{host}", command]
        completed = run_tracked(args, timeout=timeout)
        return json.dumps(_result(completed, timeout), ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        return json.dumps({"ok": False, "state": "not_started", "error": str(exc)}, indent=2)


def _copy(direction: str, host: str, username: str, remote_path: str, local_path: str, port: int, identity_file: str, known_hosts_file: str, timeout: int) -> str:
    executable = shutil.which("scp")
    if not executable:
        return json.dumps({"ok": False, "state": "not_started", "error": "OpenSSH scp client not found"}, indent=2)
    try:
        host, username = _validate("host", host), _validate("username", username)
        if not (remote_path or "").strip() or "\x00" in remote_path:
            raise ValueError("remote_path is required and cannot contain NUL")
        local = Path(local_path).expanduser().resolve()
        if direction == "to" and not local.is_file():
            raise ValueError(f"local source file not found: {local}")
        if direction == "from":
            local.parent.mkdir(parents=True, exist_ok=True)
        timeout = max(1, min(int(timeout), 1800))
        options = _options(port, identity_file, known_hosts_file, timeout)
        # scp spells its port option with uppercase P.
        options[options.index("-p")] = "-P"
        remote = f"{username}@{host}:{remote_path}"
        args = [executable, "-s", *options, "--", str(local), remote] if direction == "to" else [executable, "-s", *options, "--", remote, str(local)]
        completed = run_tracked(args, timeout=timeout)
        result = _result(completed, timeout)
        result.update(direction=direction, local_path=str(local), remote_path=remote_path)
        if direction == "from" and result["ok"]:
            result["local_bytes"] = local.stat().st_size if local.is_file() else None
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        return json.dumps({"ok": False, "state": "not_started", "error": str(exc)}, indent=2)


def ssh_copy_to(host: str, username: str, local_path: str, remote_path: str, port: int = 22, identity_file: str = "", known_hosts_file: str = "", timeout: int = 300) -> str:
    return _copy("to", host, username, remote_path, local_path, port, identity_file, known_hosts_file, timeout)


def ssh_copy_from(host: str, username: str, remote_path: str, local_path: str, port: int = 22, identity_file: str = "", known_hosts_file: str = "", timeout: int = 300) -> str:
    return _copy("from", host, username, remote_path, local_path, port, identity_file, known_hosts_file, timeout)


def register(reg):
    from seven.tools.registry import Tool
    connection = {
        "host": {"type": "string"}, "username": {"type": "string"},
        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
        "identity_file": {"type": "string"}, "known_hosts_file": {"type": "string"},
        "timeout": {"type": "integer", "minimum": 1, "maximum": 1800},
    }
    reg.register(Tool("ssh_status", "Report local OpenSSH clients and enforced authentication/host-key policy.", {"type": "object", "properties": {}}, ssh_status))
    reg.register(Tool("ssh_run", "Run a real noninteractive remote command using strict host-key verification and agent/key authentication.", {"type": "object", "properties": {**connection, "command": {"type": "string"}}, "required": ["host", "username", "command"]}, ssh_run))
    reg.register(Tool("ssh_copy_to", "Copy one local file to a remote host using strict OpenSSH scp.", {"type": "object", "properties": {**connection, "local_path": {"type": "string"}, "remote_path": {"type": "string"}}, "required": ["host", "username", "local_path", "remote_path"]}, ssh_copy_to))
    reg.register(Tool("ssh_copy_from", "Copy one remote file to a local path using strict OpenSSH scp.", {"type": "object", "properties": {**connection, "local_path": {"type": "string"}, "remote_path": {"type": "string"}}, "required": ["host", "username", "local_path", "remote_path"]}, ssh_copy_from))
