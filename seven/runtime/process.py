"""Subprocess execution that owns and cleans up the complete process tree."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Mapping, Sequence

import psutil


@dataclass
class ProcessResult:
    args: str | Sequence[str]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    terminated_pids: tuple[int, ...] = ()


def terminate_process_tree(pid: int, grace_seconds: float = 2.0) -> tuple[int, ...]:
    """Terminate descendants before their parent, then kill survivors."""
    try:
        parent = psutil.Process(pid)
    except psutil.Error:
        return ()
    processes = parent.children(recursive=True) + [parent]
    terminated = tuple(proc.pid for proc in processes)
    for proc in reversed(processes):
        try:
            proc.terminate()
        except psutil.Error:
            pass
    _, alive = psutil.wait_procs(processes, timeout=max(0.1, grace_seconds))
    for proc in alive:
        try:
            proc.kill()
        except psutil.Error:
            pass
    psutil.wait_procs(alive, timeout=max(0.1, grace_seconds))
    return terminated


def run_tracked(
    args: str | Sequence[str],
    *,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 60,
    shell: bool = False,
    encoding: str = "utf-8",
) -> ProcessResult:
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        start_new_session = True
    process = subprocess.Popen(
        args,
        shell=shell,
        cwd=cwd,
        env=dict(env) if env is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding=encoding,
        errors="replace",
        creationflags=creationflags,
        start_new_session=start_new_session,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return ProcessResult(args, process.returncode, stdout or "", stderr or "")
    except subprocess.TimeoutExpired:
        terminated = terminate_process_tree(process.pid)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return ProcessResult(
            args, process.returncode, stdout or "", stderr or "",
            timed_out=True, terminated_pids=terminated,
        )
