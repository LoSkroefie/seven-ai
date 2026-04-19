"""
Seven ↔ opencode subprocess wrapper (v3.2.20).

Wraps the `opencode` CLI (https://github.com/sst/opencode). Seven delegates
tasks to opencode without reimplementing any of its functionality.

Key choices:
- `run()` is synchronous — the caller is expected to handle timeouts / UI.
- Default agent is 'plan' (read-only analysis). The 'build' agent is
  destructive and must be explicitly enabled via config.OPENCODE_ALLOW_BUILD.
- Uses `opencode run <message>` (one-shot). Interactive sessions require
  a TTY and aren't suitable for subprocess wrap.
- Output is captured verbatim; no JSON parsing in v1. The agent's natural
  text output is what the user sees in reply.
- No API key is passed in — opencode reads its own provider config from
  ~/.config/opencode/. Seven only orchestrates invocation.

Offline-first caveat: opencode itself may call a cloud provider depending on
the user's opencode config. This wrapper does NOT introduce a cloud
dependency — it just runs whatever opencode is already configured for.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OpencodeClient")

# Agents supported by opencode 1.4.x. Keep this list in sync with
# `opencode run --agent <name>` valid values. 'plan' = read-only analysis,
# 'build' = can modify files.
AGENT_PLAN = "plan"
AGENT_BUILD = "build"
VALID_AGENTS = {AGENT_PLAN, AGENT_BUILD}


class OpencodeClient:
    """Subprocess-level wrapper around the opencode CLI."""

    def __init__(self, executable: Optional[str] = None, default_cwd: Optional[str] = None):
        """
        Args:
            executable: path to the opencode binary. If None, resolved via PATH.
            default_cwd: working directory for opencode. If None, uses Seven's cwd.
        """
        self.executable: Optional[str] = executable or shutil.which("opencode")
        self.default_cwd: Optional[str] = default_cwd
        self.available: bool = self.executable is not None
        if self.available:
            logger.info(f"[OPENCODE] resolved to {self.executable}")
        else:
            logger.info("[OPENCODE] not on PATH — install via `npm install -g opencode-ai`")

    # ------------------------------------------------------------------ api

    def get_version(self) -> Optional[str]:
        """Return the installed opencode version string, or None if unavailable."""
        if not self.available:
            return None
        try:
            r = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return (r.stdout or r.stderr or "").strip() or None
        except Exception as e:
            logger.debug(f"[OPENCODE] --version failed: {e}")
            return None

    def run(
        self,
        message: str,
        agent: str = AGENT_PLAN,
        cwd: Optional[str] = None,
        timeout: int = 180,
        model: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Invoke `opencode run` with a single message and return the result.

        Args:
            message: the prompt / task to hand to opencode.
            agent: which agent to use ('plan' for analysis, 'build' to modify files).
            cwd: working directory override. Falls back to `self.default_cwd`
                 then to the current process's cwd.
            timeout: seconds before we kill the subprocess.
            model: optional provider/model override, e.g. 'anthropic/claude-sonnet-4'.
            extra_args: extra CLI flags appended verbatim (advanced use only).

        Returns:
            Dict with keys: status, output, stderr, elapsed, cmd, returncode.
            status is one of: 'ok', 'unavailable', 'timeout', 'error'.
        """
        if not self.available:
            return {
                "status": "unavailable",
                "output": "",
                "stderr": "opencode binary not found on PATH",
                "elapsed": 0.0,
                "cmd": None,
                "returncode": None,
            }

        if agent not in VALID_AGENTS:
            return {
                "status": "error",
                "output": "",
                "stderr": f"unknown agent: {agent!r} (valid: {sorted(VALID_AGENTS)})",
                "elapsed": 0.0,
                "cmd": None,
                "returncode": None,
            }

        if not (message or "").strip():
            return {
                "status": "error",
                "output": "",
                "stderr": "empty message",
                "elapsed": 0.0,
                "cmd": None,
                "returncode": None,
            }

        cmd: List[str] = [self.executable, "run", "--agent", agent]
        if model:
            cmd.extend(["--model", model])
        resolved_cwd = cwd or self.default_cwd
        if resolved_cwd:
            cmd.extend(["--dir", str(resolved_cwd)])
        if extra_args:
            cmd.extend(list(extra_args))
        cmd.append(message)

        logger.info(
            f"[OPENCODE] run agent={agent} timeout={timeout}s "
            f"cwd={resolved_cwd or '(cwd)'}"
        )
        t0 = time.time()
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=resolved_cwd,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            elapsed = time.time() - t0
            status = "ok" if r.returncode == 0 else "error"
            return {
                "status": status,
                "output": (r.stdout or "").strip(),
                "stderr": (r.stderr or "").strip(),
                "elapsed": round(elapsed, 2),
                "cmd": cmd,
                "returncode": r.returncode,
            }
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - t0
            logger.warning(f"[OPENCODE] timeout after {timeout}s")
            return {
                "status": "timeout",
                "output": (e.stdout.decode("utf-8", "replace") if e.stdout else "").strip(),
                "stderr": f"opencode timed out after {timeout}s",
                "elapsed": round(elapsed, 2),
                "cmd": cmd,
                "returncode": None,
            }
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"[OPENCODE] run failed: {e}")
            return {
                "status": "error",
                "output": "",
                "stderr": str(e)[:500],
                "elapsed": round(elapsed, 2),
                "cmd": cmd,
                "returncode": None,
            }

    # ---------------------------------------------------------------- status

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "executable": self.executable,
            "version": self.get_version() if self.available else None,
            "default_cwd": self.default_cwd,
        }
