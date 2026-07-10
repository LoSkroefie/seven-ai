"""
Always-on Seven daemon.
- Keeps process alive
- Heartbeat + world/self refresh
- Optional local API
- Writes PID file for status/stop
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import time
from pathlib import Path

from seven import config, __version__
from seven.agent.loop import Seven

logger = logging.getLogger("seven.daemon")


def pid_path() -> Path:
    return config.DATA_DIR / "seven.pid"


def write_pid():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    pid_path().write_text(str(os.getpid()), encoding="utf-8")


def clear_pid():
    try:
        pid_path().unlink(missing_ok=True)
    except Exception:
        pass


def read_pid() -> int | None:
    p = pid_path()
    if not p.exists():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip())
    except Exception:
        return None


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


def run_daemon(enable_api: bool = True, tick_seconds: float | None = None):
    """
    Blocking daemon loop.
    tick_seconds overrides HEARTBEAT for the outer sleep (still runs autonomy heartbeat).
    """
    tick = float(tick_seconds or config.HEARTBEAT_SECONDS)
    # Faster sense cadence than heavy work: at least every 60s for world refresh
    sense_every = min(tick, float(getattr(config, "DAEMON_SENSE_SECONDS", 60)))

    existing = read_pid()
    if existing and is_pid_running(existing) and existing != os.getpid():
        print(f"Seven daemon already running (pid={existing}). Stop it first: python -m seven --daemon-stop")
        return 1

    write_pid()
    agent = Seven()
    agent.start_heartbeat()

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
    pid = read_pid()
    if not pid:
        print("No PID file — daemon not running?")
        return 1
    if not is_pid_running(pid):
        print(f"Stale PID {pid}; removing.")
        clear_pid()
        return 0
    print(f"Stopping Seven daemon pid={pid}…")
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:
        print(f"Stop failed: {e}")
        return 1
    clear_pid()
    print("Stopped.")
    return 0


def daemon_status() -> str:
    pid = read_pid()
    lines = [f"Seven Real {__version__} daemon status"]
    if pid and is_pid_running(pid):
        lines.append(f"running pid={pid}")
    elif pid:
        lines.append(f"stale pid={pid} (not running)")
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
