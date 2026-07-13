import json
import logging
import os
import subprocess
import sys
import time

import psutil

from seven.runtime import daemon


def test_unowned_pid_is_never_signaled(tmp_path, monkeypatch):
    monkeypatch.setattr(daemon.config, "DATA_DIR", tmp_path)
    record = daemon._process_record(os.getpid())
    daemon.write_pid(record)
    assert daemon.is_daemon_record(record) is False
    assert daemon.stop_daemon() == 0
    assert psutil.pid_exists(os.getpid())
    assert daemon.read_pid_record() is None


def test_owned_daemon_lease_duplicate_status_and_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(daemon.config, "DATA_DIR", tmp_path)
    env = os.environ.copy()
    env["SEVEN_DATA_DIR"] = str(tmp_path)
    code = "from seven.runtime.daemon import claim_pid; import time; print(claim_pid(), flush=True); time.sleep(60)"
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    child = subprocess.Popen(
        [sys.executable, "-c", code, "--daemon"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=flags,
        start_new_session=os.name != "nt",
    )
    try:
        line = child.stdout.readline()
        assert "True" in line
        record = daemon.read_pid_record()
        # Some Windows Python launchers hand off to a child interpreter, so the
        # authoritative PID is the process that atomically wrote the lease.
        assert psutil.pid_exists(record["pid"])
        assert daemon.is_daemon_record(record) is True
        assert "running pid=" in daemon.daemon_status()
        claimed, duplicate = daemon.claim_pid()
        assert claimed is False and duplicate["pid"] == record["pid"]
        assert daemon.stop_daemon() == 0
        assert child.wait(timeout=10) is not None
        assert daemon.read_pid_record() is None
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_rotating_file_logging(tmp_path, monkeypatch):
    import seven.__main__ as entry
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    for handler in old_handlers:
        root.removeHandler(handler)
    try:
        monkeypatch.setattr(entry.config, "DATA_DIR", tmp_path)
        monkeypatch.setattr(entry.config, "LOG_PATH", tmp_path / "seven.log")
        monkeypatch.setattr(entry.config, "LOG_MAX_BYTES", 1024)
        monkeypatch.setattr(entry.config, "LOG_BACKUP_COUNT", 2)
        entry.setup_logging()
        logging.getLogger("rotation-proof").warning("x" * 800)
        logging.getLogger("rotation-proof").warning("y" * 800)
        for handler in root.handlers:
            handler.flush()
        assert (tmp_path / "seven.log").exists()
        assert (tmp_path / "seven.log.1").exists()
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
        for handler in old_handlers:
            root.addHandler(handler)
