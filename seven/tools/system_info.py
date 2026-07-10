"""Host system facts."""
from __future__ import annotations

import os
import platform
import socket
from datetime import datetime


def get_system_info() -> str:
    lines = [
        f"time={datetime.now().isoformat(timespec='seconds')}",
        f"os={platform.system()} {platform.release()} ({platform.version()})",
        f"machine={platform.machine()}",
        f"processor={platform.processor()}",
        f"hostname={socket.gethostname()}",
        f"user={os.environ.get('USERNAME') or os.environ.get('USER')}",
        f"cwd={os.getcwd()}",
        f"python={platform.python_version()}",
        f"home={os.path.expanduser('~')}",
    ]
    try:
        import psutil
        vm = psutil.virtual_memory()
        lines.append(f"ram_total_gb={vm.total/1e9:.1f} ram_used_pct={vm.percent}")
        lines.append(f"cpu_count={psutil.cpu_count()} cpu_pct={psutil.cpu_percent(interval=0.3)}")
        bat = None
        try:
            bat = psutil.sensors_battery()
        except Exception:
            pass
        if bat:
            lines.append(f"battery_pct={bat.percent} charging={bat.power_plugged}")
    except ImportError:
        lines.append("psutil=not_installed")
    return "\n".join(lines)


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="get_system_info",
        description="Get current host system info (OS, RAM, CPU, time, user).",
        parameters={"type": "object", "properties": {}},
        handler=lambda: get_system_info(),
    ))
