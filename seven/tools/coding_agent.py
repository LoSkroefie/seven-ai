"""
Delegate to local coding CLIs when installed: opencode, claude, codex.
Legitimate local binaries only — no stolen free endpoints.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

from seven import config


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def coding_agent_status() -> str:
    found = []
    for n in ("opencode", "claude", "codex", "aider"):
        p = _which(n)
        if p:
            found.append(f"{n}={p}")
    return "installed: " + (", ".join(found) if found else "none")


def run_opencode(prompt: str, agent: str = "plan", cwd: Optional[str] = None) -> str:
    exe = _which("opencode")
    if not exe:
        return "ERROR: opencode not on PATH. Install: npm i -g opencode-ai (or your distro package)"
    if agent == "build" and not config.OPENCODE_ALLOW_BUILD:
        return "ERROR: build agent disabled. Set SEVEN_OPENCODE_BUILD=1 to enable."
    cwd = cwd or str(config.WORKSPACE_DIR)
    # opencode CLI variants differ; try common forms
    attempts = [
        [exe, "run", "--agent", agent, prompt],
        [exe, "run", prompt],
        [exe, prompt],
    ]
    last_err = ""
    for cmd in attempts:
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.OPENCODE_TIMEOUT,
                cwd=cwd,
                env=os.environ.copy(),
            )
            out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
            if r.returncode == 0 or out.strip():
                return f"cmd={' '.join(cmd)}\nexit={r.returncode}\n{out[:8000]}"
            last_err = out or f"exit {r.returncode}"
        except subprocess.TimeoutExpired:
            return f"ERROR: opencode timed out after {config.OPENCODE_TIMEOUT}s"
        except Exception as e:
            last_err = str(e)
    return f"ERROR running opencode: {last_err}"


def run_claude_cli(prompt: str, cwd: Optional[str] = None) -> str:
    exe = _which("claude")
    if not exe:
        return "ERROR: claude CLI not on PATH (Anthropic Claude Code)."
    cwd = cwd or str(config.WORKSPACE_DIR)
    try:
        r = subprocess.run(
            [exe, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=config.OPENCODE_TIMEOUT,
            cwd=cwd,
            env=os.environ.copy(),
        )
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return f"exit={r.returncode}\n{out[:8000]}"
    except Exception as e:
        return f"ERROR: {e}"


def run_codex_cli(prompt: str, cwd: Optional[str] = None) -> str:
    exe = _which("codex")
    if not exe:
        return "ERROR: codex CLI not on PATH."
    cwd = cwd or str(config.WORKSPACE_DIR)
    try:
        r = subprocess.run(
            [exe, prompt],
            capture_output=True,
            text=True,
            timeout=config.OPENCODE_TIMEOUT,
            cwd=cwd,
            env=os.environ.copy(),
        )
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return f"exit={r.returncode}\n{out[:8000]}"
    except Exception as e:
        return f"ERROR: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="coding_agent_status",
        description="List which external coding CLIs are installed (opencode, claude, codex, aider).",
        parameters={"type": "object", "properties": {}},
        handler=lambda: coding_agent_status(),
    ))
    reg.register(Tool(
        name="run_opencode",
        description="Delegate a coding task to the local opencode CLI.",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "agent": {"type": "string", "description": "plan|build"},
                "cwd": {"type": "string"},
            },
            "required": ["prompt"],
        },
        handler=run_opencode,
    ))
    reg.register(Tool(
        name="run_claude_cli",
        description="Delegate to local Anthropic Claude Code CLI if installed and authenticated.",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "cwd": {"type": "string"},
            },
            "required": ["prompt"],
        },
        handler=run_claude_cli,
    ))
    reg.register(Tool(
        name="run_codex_cli",
        description="Delegate to local OpenAI Codex CLI if installed and authenticated.",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "cwd": {"type": "string"},
            },
            "required": ["prompt"],
        },
        handler=run_codex_cli,
    ))
