import json
import time
import wave

import pytest

from seven.tools.music import LocalMusicPlayer
import seven.tools.music as music_module


def _silence(path, seconds=3):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * int(8000 * seconds))


def test_missing_unsupported_and_unavailable_are_not_success(tmp_path, monkeypatch):
    player = LocalMusicPlayer(tmp_path / "runtime")
    assert player.play(str(tmp_path / "missing.mp3"))["state"] == "not_started"
    bad = tmp_path / "not-audio.txt"
    bad.write_text("no", encoding="utf-8")
    assert "unsupported" in player.play(str(bad))["error"]
    audio = tmp_path / "valid.wav"
    _silence(audio, 1)
    monkeypatch.setattr(player, "backend", lambda: None)
    result = player.play(str(audio))
    assert result["ok"] is False
    assert result["state"] == "not_started"


def test_stop_when_idle_is_truthful(tmp_path):
    player = LocalMusicPlayer(tmp_path / "runtime")
    result = player.stop()
    assert result["ok"] is True
    assert "nothing owned" in result["message"]


def test_restart_reclaims_only_proven_worker(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    control = runtime / "control.json"
    (runtime / "state.json").write_text('{"state":"playing","pid":321}', encoding="utf-8")

    class PriorWorker:
        def cmdline(self):
            return ["python", "-m", "seven.runtime.audio_worker", "--control", str(control)]

    terminated = []
    monkeypatch.setattr(music_module.psutil, "Process", lambda pid: PriorWorker())
    monkeypatch.setattr(music_module, "terminate_process_tree", lambda pid: terminated.append(pid))
    player = LocalMusicPlayer(runtime)
    assert terminated == [321]
    assert player.status()["state"] == "recovered_orphan"


def test_real_silent_worker_play_pause_resume_stop(tmp_path, monkeypatch):
    pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    audio = tmp_path / "silence.wav"
    _silence(audio)
    player = LocalMusicPlayer(tmp_path / "runtime")
    assert player.backend() == "pygame-worker"
    started = player.play(str(audio))
    try:
        assert started["ok"] is True
        assert started["state"] == "playing"
        pid = started["pid"]
        paused = player.pause()
        assert paused["ok"] is True and paused["state"] == "paused"
        resumed = player.resume()
        assert resumed["ok"] is True and resumed["state"] == "playing"
        stopped = player.stop()
        assert stopped["ok"] is True and stopped["state"] == "stopped"
        assert stopped["terminated_pid"] == pid
        assert player.process.poll() == 0
    finally:
        player.stop()


def test_real_worker_reports_natural_finish(tmp_path, monkeypatch):
    pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    audio = tmp_path / "short.wav"
    _silence(audio, 0.2)
    player = LocalMusicPlayer(tmp_path / "runtime")
    assert player.play(str(audio))["ok"] is True
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and player.status()["state"] == "playing":
        time.sleep(0.05)
    assert player.status()["state"] == "finished"
