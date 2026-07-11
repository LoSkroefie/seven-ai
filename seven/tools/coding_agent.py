"""Delegate real work to installed, authenticated local coding-agent CLIs."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional, Sequence

from seven import config
from seven.runtime.process import ProcessResult, run_tracked


AGENTS = ("opencode", "claude", "codex", "aider")


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def _shim_command(executable: str, args: Sequence[str]) -> list[str]:
    """Run Windows PowerShell/cmd shims explicitly; use binaries directly elsewhere."""
    suffix = Path(executable).suffix.lower()
    if os.name == "nt" and suffix == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", executable, *args]
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", executable, *args]
    return [executable, *args]


def _format(result: ProcessResult, command: Sequence[str]) -> str:
    payload = {
        "command": list(command),
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "terminated_processes": list(result.terminated_pids),
        "stdout": result.stdout[-40000:],
        "stderr": result.stderr[-10000:],
    }
    prefix = "ERROR: " if result.timed_out or result.returncode not in (0, None) else ""
    return prefix + json.dumps(payload, ensure_ascii=False, indent=2)


def _run(name: str, args: Sequence[str], cwd: Optional[str]) -> str:
    executable = _which(name)
    if not executable:
        return f"ERROR: {name} is not installed or not on PATH"
    work = str(Path(cwd or config.WORKSPACE_DIR).expanduser().resolve())
    Path(work).mkdir(parents=True, exist_ok=True)
    command = _shim_command(executable, list(args))
    try:
        result = run_tracked(
            command, cwd=work, env=os.environ.copy(),
            timeout=config.OPENCODE_TIMEOUT,
        )
        return _format(result, command)
    except Exception as exc:
        return f"ERROR: {name} failed to start: {exc}"


def coding_agent_status() -> str:
    status = {}
    for name in AGENTS:
        executable = _which(name)
        if not executable:
            status[name] = {"installed": False}
            continue
        command = _shim_command(executable, ["--version"])
        try:
            result = run_tracked(command, timeout=20, env=os.environ.copy())
            status[name] = {
                "installed": True,
                "path": executable,
                "version": (result.stdout or result.stderr).strip().splitlines()[0],
                "ok": result.returncode == 0 and not result.timed_out,
            }
        except Exception as exc:
            status[name] = {"installed": True, "path": executable, "ok": False, "error": str(exc)}
    return json.dumps(status, indent=2)


def run_opencode(prompt: str, agent: str = "build", cwd: Optional[str] = None) -> str:
    if agent == "build" and not config.OPENCODE_ALLOW_BUILD:
        return "ERROR: OpenCode build agent is disabled by SEVEN_OPENCODE_BUILD"
    if agent not in {"plan", "build"}:
        return "ERROR: agent must be plan or build"
    return _run("opencode", ["run", "--agent", agent, prompt], cwd)


def run_claude_cli(prompt: str, cwd: Optional[str] = None) -> str:
    args = ["--print"]
    if config.CODING_AGENT_UNRESTRICTED:
        args.append("--dangerously-skip-permissions")
    args.append(prompt)
    return _run("claude", args, cwd)


def run_codex_cli(prompt: str, cwd: Optional[str] = None) -> str:
    args = ["exec", "--skip-git-repo-check"]
    if config.CODING_AGENT_UNRESTRICTED:
        args.append("--dangerously-bypass-approvals-and-sandbox")
    args.append(prompt)
    return _run("codex", args, cwd)


def run_aider(prompt: str, cwd: Optional[str] = None) -> str:
    return _run("aider", ["--yes-always", "--message", prompt], cwd)


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="coding_agent_status",
        description="Report installed OpenCode, Claude Code, Codex and Aider CLIs with versions.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: coding_agent_status(),
    ))
    for name, description, handler, extra in (
        ("run_opencode", "Delegate a coding task to OpenCode's non-interactive run command.", run_opencode, {"agent": {"type": "string", "enum": ["plan", "build"]}}),
        ("run_claude_cli", "Delegate a coding task to Claude Code non-interactively.", run_claude_cli, {}),
        ("run_codex_cli", "Delegate a coding task to Codex exec non-interactively.", run_codex_cli, {}),
        ("run_aider", "Delegate a coding task to Aider non-interactively.", run_aider, {}),
    ):
        properties = {"prompt": {"type": "string"}, "cwd": {"type": "string"}, **extra}
        reg.register(Tool(
            name=name,
            description=description,
            parameters={"type": "object", "properties": properties, "required": ["prompt"]},
            handler=handler,
        ))
