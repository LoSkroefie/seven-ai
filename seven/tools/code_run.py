"""Run Python code in a subprocess."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from seven import config
from seven.runtime.process import run_tracked


def run_python(code: str, timeout: int = 60) -> str:
    work = config.WORKSPACE_DIR
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=str(work), encoding="utf-8"
    ) as f:
        f.write(code)
        path = f.name
    try:
        completed = run_tracked(
            [sys.executable, path],
            timeout=timeout,
            cwd=str(work),
            env=os.environ.copy(),
        )
        parts = [f"exit_code={completed.returncode}", f"script={path}"]
        if completed.stdout:
            parts.append("STDOUT:\n" + completed.stdout)
        if completed.stderr:
            parts.append("STDERR:\n" + completed.stderr)
        if not completed.stdout and not completed.stderr:
            parts.append("(no output)")
        if completed.timed_out:
            parts.append(
                f"ERROR: python timed out after {timeout}s; "
                f"terminated_processes={list(completed.terminated_pids)}"
            )
        return "\n".join(parts)
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="run_python",
        description="Execute a Python code snippet in a subprocess. Returns stdout/stderr.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "timeout": {"type": "integer"},
            },
            "required": ["code"],
        },
        handler=run_python,
    ))
