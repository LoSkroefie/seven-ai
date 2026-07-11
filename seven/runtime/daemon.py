"""
Always-on Seven daemon.
- Keeps process alive
- Heartbeat + world/self refresh
- Optional local API
- Writes PID file for status/stop
"""
from __future__ import annotations

import logging
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from seven import config, __version__
from seven.agent.loop import Seven
from seven.runtime.process import terminate_process_tree
import psutil

logger = logging.getLogger("seven.daemon")


def pid_path(data_dir: Path | None = None) -> Path:
    return Path(data_dir or config.DATA_DIR) / "seven.pid"


def _process_record(pid: int | None = None) -> dict:
    pid = int(pid or os.getpid())
    return {
        "pid": pid,
        "create_time": psutil.Process(pid).create_time(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
    }


def read_pid_record(data_dir: Path | None = None) -> dict | None:
    path = pid_path(data_dir)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
        if text.startswith("{"):
            data = json.loads(text)
            return data if int(data.get("pid", 0)) > 0 else None
        # Legacy integer PID files have no process-birth proof and are stale.
        return {"pid": int(text), "legacy": True}
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def write_pid(record: dict | None = None):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = record or _process_record()
    temp = pid_path().with_suffix(".pid.tmp")
    temp.write_text(json.dumps(record), encoding="utf-8")
    os.replace(temp, pid_path())


def claim_pid() -> tuple[bool, dict]:
    """Atomically claim daemon ownership, replacing only stale/unowned records."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = _process_record()
    payload = json.dumps(record).encode("utf-8")
    for _ in range(2):
        try:
            fd = os.open(pid_path(), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
            return True, record
        except FileExistsError:
            existing = read_pid_record()
            if existing and is_daemon_record(existing):
                return False, existing
            clear_pid()
    return False, read_pid_record() or {}


def clear_pid():
    try:
        pid_path().unlink(missing_ok=True)
    except Exception:
        pass


def read_pid(data_dir: Path | None = None) -> int | None:
    record = read_pid_record(data_dir)
    return int(record["pid"]) if record else None


def is_pid_running(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        # Windows: os.kill(pid, 0) doesn't work the same; try OpenProcess via psutil only
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False


def is_daemon_record(record: dict) -> bool:
    """Require PID, matching birth time, and Seven daemon command line."""
    if not record or record.get("legacy"):
        return False
    try:
        process = psutil.Process(int(record["pid"]))
        if abs(process.create_time() - float(record["create_time"])) > 0.01:
            return False
        command = " ".join(process.cmdline()).lower()
        return "--daemon" in command and ("seven" in command or "seven.runtime.daemon" in command)
    except (psutil.Error, KeyError, TypeError, ValueError):
        return False


def run_daemon(enable_api: bool = False, tick_seconds: float | None = None):
    """
    Blocking daemon loop.
    tick_seconds overrides HEARTBEAT for the outer sleep (still runs autonomy heartbeat).
    """
    tick = max(1.0, float(tick_seconds or config.HEARTBEAT_SECONDS))
    # Faster sense cadence than heavy work: at least every 60s for world refresh
    sense_every = min(tick, float(getattr(config, "DAEMON_SENSE_SECONDS", 60)))

    claimed, record = claim_pid()
    if not claimed:
        existing = record.get("pid")
        print(f"Seven daemon already running (pid={existing}). Stop it first: python -m seven --daemon-stop")
        return 1
    try:
        agent = Seven()
        agent.start_heartbeat()
    except Exception:
        clear_pid()
        raise

    api_server = None
    if enable_api or config.ENABLE_API:
        try:
            from seven.ui.api_server import start_api_server
            api_server = start_api_server(background=True, agent=agent)
            logger.info("Daemon API http://%s:%s", config.API_HOST, config.API_PORT)
        except Exception:
            logger.exception("API failed to start")

    stop = False

    def _stop(*_args):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    try:
        signal.signal(signal.SIGTERM, _stop)
    except Exception:
        pass

    print("=" * 60)
    print(f"  Seven Real {__version__} — DAEMON")
    print(f"  pid={os.getpid()}  data={config.DATA_DIR}")
    print(f"  sense every {sense_every}s  heartbeat={config.HEARTBEAT_SECONDS}s")
    if enable_api or config.ENABLE_API:
        print(f"  API http://{config.API_HOST}:{config.API_PORT}")
    print("  Ctrl+C to stop")
    print("=" * 60)

    # Initial sense
    try:
        agent.refresh_living_state()
        logger.info("Initial world/self:\n%s", agent.living.status_text())
    except Exception:
        logger.exception("initial sense failed")

    last_sense = 0.0
    try:
        while not stop:
            now = time.time()
            if now - last_sense >= sense_every:
                try:
                    agent.refresh_living_state()
                    # Light autonomous tick outside heartbeat thread too (belt+suspenders)
                    # Prefer heartbeat thread; here only re-sense + save
                    last_sense = now
                except Exception:
                    logger.exception("daemon sense failed")
            time.sleep(1.0)
    finally:
        logger.info("Daemon shutting down")
        try:
            agent.shutdown()
        except Exception:
            pass
        if api_server is not None:
            try:
                api_server.shutdown()
            except Exception:
                pass
        clear_pid()
        print("Daemon stopped.")
    return 0


def stop_daemon() -> int:
    record = read_pid_record()
    if not record:
        print("No PID file — daemon not running?")
        return 0
    pid = int(record["pid"])
    if not is_daemon_record(record):
        print(f"Stale or unowned PID record {pid}; removing without signaling it.")
        clear_pid()
        return 0
    print(f"Stopping Seven daemon pid={pid}…")
    try:
        terminated = terminate_process_tree(pid, grace_seconds=10)
        if not terminated:
            raise RuntimeError("owned daemon disappeared before termination could be confirmed")
    except Exception as e:
        print(f"Stop failed: {e}")
        return 1
    if is_daemon_record(record):
        print("Stop failed: owned daemon is still running; PID record preserved.")
        return 1
    clear_pid()
    print("Stopped.")
    return 0


def daemon_status() -> str:
    record = read_pid_record()
    pid = int(record["pid"]) if record else None
    lines = [f"Seven Real {__version__} daemon status"]
    if record and is_daemon_record(record):
        lines.append(f"running pid={pid}")
        lines.append(f"started_at={record.get('started_at')} version={record.get('version')}")
    elif pid:
        lines.append(f"stale_or_unowned pid={pid} (will not be signaled)")
    else:
        lines.append("not running")
    state_path = config.DATA_DIR / "living_state.json"
    if state_path.exists():
        lines.append(f"living_state={state_path}")
        try:
            import json
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self_st = data.get("self") or {}
            st = self_st.get("state") or {}
            lines.append(f"mode={st.get('mode')} energy={st.get('energy')} ticks={data.get('tick_count')}")
            lines.append(f"intent={self_st.get('intent')}")
            lines.append(f"last_action={data.get('last_action')}")
        except Exception as e:
            lines.append(f"state_read_error={e}")
    return "\n".join(lines)


def restart_daemon(enable_api: bool = False) -> int:
    result = stop_daemon()
    if result != 0:
        return result
    return run_daemon(enable_api=enable_api)
