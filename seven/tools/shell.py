"""Shell execution — L4 unrestricted with audit. Windows-aware."""
from __future__ import annotations

import os
import platform
from typing import Optional

from seven import config
from seven.runtime.process import run_tracked
from seven.tools.sanitize import coerce_int, is_blank


def _prepare_command(command: str) -> str:
    """
    Light normalization for model-generated commands.
    Does not sandbox — L4. Helps common quoting footguns.
    """
    command = (command or "").strip()
    if not command:
        return command
    # Strip accidental markdown fences
    if command.startswith("```"):
        lines = command.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        command = "\n".join(lines).strip()
    return command


def run_shell(command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> str:
    if is_blank(command):
        return "ERROR: command is required"
    command = _prepare_command(str(command))
    if is_blank(cwd):
        cwd = None
    cwd = cwd or config.SHELL_DEFAULT_CWD
    timeout = coerce_int(timeout, config.SHELL_TIMEOUT) or config.SHELL_TIMEOUT

    if not os.path.isdir(cwd):
        try:
            os.makedirs(cwd, exist_ok=True)
        except OSError as e:
            return f"ERROR: cannot create cwd {cwd}: {e}"

    env = os.environ.copy()
    # Prefer UTF-8 output on Windows where possible
    env.setdefault("PYTHONIOENCODING", "utf-8")

    try:
        # On Windows, shell=True uses COMSPEC (cmd.exe). PowerShell-native
        # syntax often fails — document that in the error if we detect it.
        completed = run_tracked(
            command,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
            encoding="utf-8",
        )
        out = completed.stdout or ""
        err = completed.stderr or ""
        parts = [
            f"exit_code={completed.returncode}",
            f"cwd={cwd}",
            f"shell={env.get('COMSPEC') or env.get('SHELL') or 'default'}",
        ]
        if out:
            parts.append("STDOUT:\n" + out)
        if err:
            parts.append("STDERR:\n" + err)
        if not out and not err:
            parts.append("(no output)")
        if completed.timed_out:
            parts.append(
                f"ERROR: command timed out after {timeout}s; "
                f"terminated_processes={list(completed.terminated_pids)}"
            )
        if completed.returncode != 0 and platform.system() == "Windows":
            if any(tok in command for tok in ("Get-", "Write-Host", "$", " | ")):
                parts.append(
                    "HINT: Windows default shell is cmd.exe. "
                    "For PowerShell, prefix with: powershell -NoProfile -Command \"...\""
                )
        return "\n".join(parts)
    except Exception as e:
        return f"ERROR: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="run_shell",
        description=(
            "Execute a shell command on the host OS. "
            "On Windows this is cmd.exe by default — for PowerShell use: "
            "powershell -NoProfile -Command \"...\". "
            "Returns stdout/stderr/exit code."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "cwd": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "integer", "description": "Timeout seconds (optional)"},
            },
            "required": ["command"],
        },
        handler=run_shell,
        tier="core",
    ))
