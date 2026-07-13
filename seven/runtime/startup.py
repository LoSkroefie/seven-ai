"""Install/remove Seven's per-user login startup entry."""
from __future__ import annotations

import json
import os
import plistlib
import shlex
import sys
from pathlib import Path
from typing import Any


def startup_target(platform_name: str | None = None, home: Path | None = None) -> Path:
    platform_name = platform_name or sys.platform
    home = Path(home or Path.home())
    if platform_name == "win32":
        appdata = Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
        return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "Seven Talk.cmd"
    if platform_name == "darwin":
        return home / "Library" / "LaunchAgents" / "ai.seven.companion.plist"
    return home / ".config" / "autostart" / "seven-companion.desktop"


def install_startup(
    quiet: bool = False,
    platform_name: str | None = None,
    home: Path | None = None,
    python_exe: str | None = None,
) -> dict[str, Any]:
    platform_name = platform_name or sys.platform
    target = startup_target(platform_name, home)
    target.parent.mkdir(parents=True, exist_ok=True)
    python_exe = python_exe or sys.executable
    args = [python_exe, "-m", "seven", "--quiet" if quiet else "--talk"]
    if platform_name == "win32":
        quoted = " ".join(f'"{arg}"' if " " in arg or arg == python_exe else arg for arg in args)
        target.write_text("@echo off\r\nstart \"Seven\" " + quoted + "\r\n", encoding="utf-8")
    elif platform_name == "darwin":
        payload = {
            "Label": "ai.seven.companion",
            "ProgramArguments": args,
            "RunAtLoad": True,
            "KeepAlive": False,
            "ProcessType": "Interactive",
        }
        with target.open("wb") as handle:
            plistlib.dump(payload, handle)
    else:
        command = " ".join(shlex.quote(arg) for arg in args)
        target.write_text(
            "[Desktop Entry]\nType=Application\nName=Seven\n"
            f"Comment=Start Seven companion after login\nExec={command}\n"
            "Terminal=true\nX-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
        target.chmod(0o700)
    return {"ok": True, "installed": True, "path": str(target), "mode": "quiet" if quiet else "talk"}


def remove_startup(platform_name: str | None = None, home: Path | None = None) -> dict[str, Any]:
    target = startup_target(platform_name, home)
    existed = target.exists()
    target.unlink(missing_ok=True)
    return {"ok": True, "installed": False, "removed": existed, "path": str(target)}


def startup_status(platform_name: str | None = None, home: Path | None = None) -> dict[str, Any]:
    target = startup_target(platform_name, home)
    return {"ok": True, "installed": target.exists(), "path": str(target)}
