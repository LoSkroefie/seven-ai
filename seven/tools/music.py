"""Owned local audio playback with truthful lifecycle state."""
from __future__ import annotations

import importlib.util
import atexit
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from seven import config
from seven.runtime.process import terminate_process_tree
import psutil

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".opus"}


class LocalMusicPlayer:
    def __init__(self, runtime_dir: Path | None = None):
        self.runtime_dir = Path(runtime_dir or config.DATA_DIR / "runtime" / "music")
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.process: subprocess.Popen | None = None
        self.current_file: Path | None = None
        self.control = self.runtime_dir / "control.json"
        self.state_file = self.runtime_dir / "state.json"
        self._lock = threading.RLock()
        self._recover_orphan()

    def _recover_orphan(self) -> None:
        """Stop only a prior Seven worker proven by PID and exact control path."""
        if not self.state_file.exists():
            return
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            pid = int(state.get("pid") or 0)
            process = psutil.Process(pid)
            command = process.cmdline()
            marker = str(self.control)
            if "seven.runtime.audio_worker" in " ".join(command) and marker in command:
                terminate_process_tree(pid)
                self.state_file.write_text(json.dumps({"state": "recovered_orphan", "pid": pid}), encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError, psutil.Error):
            return

    @staticmethod
    def backend() -> str | None:
        if importlib.util.find_spec("pygame"):
            return "pygame-worker"
        if shutil.which("ffplay"):
            return "ffplay"
        return None

    def status(self) -> dict:
        with self._lock:
            backend = self.backend()
            state = "idle"
            detail = {}
            if self.state_file.exists():
                try:
                    detail = json.loads(self.state_file.read_text(encoding="utf-8"))
                    state = detail.get("state", "unknown")
                except (OSError, json.JSONDecodeError):
                    state = "unknown"
            if self.process and self.process.poll() is None:
                detail["pid"] = self.process.pid
            elif state in {"playing", "paused"}:
                detail["exit_code"] = self.process.returncode if self.process else None
                state = "finished" if self.process and self.process.returncode == 0 else "failed"
            return {"backend": backend, "state": state, "file": str(self.current_file) if self.current_file else None, **detail}

    def play(self, path: str) -> dict:
        audio = Path(path).expanduser().resolve()
        if not audio.is_file():
            return {"ok": False, "state": "not_started", "error": f"file not found: {audio}"}
        if audio.suffix.lower() not in AUDIO_EXTENSIONS:
            return {"ok": False, "state": "not_started", "error": f"unsupported audio type: {audio.suffix or '(none)'}"}
        backend = self.backend()
        if not backend:
            return {"ok": False, "state": "not_started", "error": "no audio backend; install seven-ai[voice] or ffplay"}
        with self._lock:
            self.stop()
            self.control.unlink(missing_ok=True)
            self.state_file.unlink(missing_ok=True)
            if backend == "pygame-worker":
                args = [sys.executable, "-m", "seven.runtime.audio_worker", "--file", str(audio), "--control", str(self.control), "--state", str(self.state_file)]
            else:
                args = [shutil.which("ffplay"), "-nodisp", "-autoexit", "-loglevel", "error", str(audio)]
            flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
            self.process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, start_new_session=os.name != "nt")
            self.current_file = audio
            if backend == "pygame-worker":
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if self.state_file.exists():
                        status = self.status()
                        if status["state"] == "playing":
                            return {"ok": True, **status}
                        if status["state"] == "error":
                            self.process.wait(timeout=2)
                            return {"ok": False, **status}
                    if self.process.poll() is not None:
                        return {"ok": False, "backend": backend, "state": "failed", "exit_code": self.process.returncode}
                    time.sleep(0.05)
                self.stop()
                return {"ok": False, "backend": backend, "state": "failed", "error": "playback worker did not become ready"}
            time.sleep(0.15)
            if self.process.poll() is not None:
                return {"ok": False, "backend": backend, "state": "failed", "exit_code": self.process.returncode}
            self._write_state("playing")
            return {"ok": True, **self.status()}

    def _write_state(self, state: str) -> None:
        self.state_file.write_text(json.dumps({"state": state, "pid": self.process.pid if self.process else None}), encoding="utf-8")

    def _command(self, command: str) -> dict:
        status = self.status()
        if status["backend"] != "pygame-worker":
            return {"ok": False, **status, "error": f"{command} requires the pygame-worker backend"}
        if not self.process or self.process.poll() is not None:
            return {"ok": False, **status, "error": "nothing is playing"}
        payload = {"id": uuid.uuid4().hex, "command": command}
        temp = self.control.with_suffix(".tmp")
        temp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(temp, self.control)
        expected = "paused" if command == "pause" else "playing"
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            status = self.status()
            if status["state"] == expected:
                return {"ok": True, **status}
            time.sleep(0.05)
        return {"ok": False, **self.status(), "error": f"worker did not acknowledge {command}"}

    def pause(self) -> dict:
        return self._command("pause")

    def resume(self) -> dict:
        return self._command("resume")

    def stop(self) -> dict:
        with self._lock:
            if not self.process or self.process.poll() is not None:
                return {"ok": True, **self.status(), "message": "nothing owned is playing"}
            pid = self.process.pid
            if self.backend() == "pygame-worker":
                payload = {"id": uuid.uuid4().hex, "command": "stop"}
                temp = self.control.with_suffix(".tmp")
                temp.write_text(json.dumps(payload), encoding="utf-8")
                os.replace(temp, self.control)
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    terminate_process_tree(pid)
            else:
                terminate_process_tree(pid)
            self._write_state("stopped")
            return {"ok": True, **self.status(), "terminated_pid": pid}


_player = LocalMusicPlayer()
atexit.register(_player.stop)


def register(reg):
    from seven.tools.registry import Tool
    def result(value): return json.dumps(value, ensure_ascii=False, indent=2)
    reg.register(Tool("music_status", "Report Seven-owned local playback and backend state.", {"type": "object", "properties": {}}, lambda: result(_player.status())))
    reg.register(Tool("play_local_audio", "Play a local audio file in a separately owned process.", {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, lambda path: result(_player.play(path))))
    reg.register(Tool("pause_local_audio", "Pause Seven-owned playback when the backend supports acknowledgement.", {"type": "object", "properties": {}}, lambda: result(_player.pause())))
    reg.register(Tool("resume_local_audio", "Resume Seven-owned paused playback when supported.", {"type": "object", "properties": {}}, lambda: result(_player.resume())))
    reg.register(Tool("stop_local_audio", "Stop only the playback process tree Seven owns.", {"type": "object", "properties": {}}, lambda: result(_player.stop())))
