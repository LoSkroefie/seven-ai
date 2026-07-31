"""Install/remove Seven's per-user login startup entry."""
from __future__ import annotations

import json
import os
import plistlib
import shlex
import sys
from pathlib import Path
from typing import Any

_STARTUP_ENV_KEYS = (
    "SEVEN_DATA_DIR",
    "SEVEN_WORKSPACE",
    "OLLAMA_URL",
    "OLLAMA_MODEL",
    "OLLAMA_VISION_MODEL",
    "SEVEN_TTS",
    "SEVEN_VOICE",
    "SEVEN_QUIET",
    "SEVEN_UNSOLICITED",
    "SEVEN_CAPTURE_MODE",
    "SEVEN_TOOL_TIER",
    "SEVEN_TOOL_SCHEMA_MODE",
    "SEVEN_BACKGROUND_LLM",
    "SEVEN_BROWSER_PROFILE",
    "SEVEN_PROJECT_ROOTS",
    "PLAYWRIGHT_BROWSERS_PATH",
    "SEVEN_SMTP_HOST",
    "SEVEN_SMTP_PORT",
    "SEVEN_SMTP_SSL",
    "SEVEN_SMTP_STARTTLS",
    "SEVEN_SMTP_USER",
    "SEVEN_EMAIL_FROM",
    "SEVEN_IMAP_HOST",
    "SEVEN_IMAP_PORT",
    "SEVEN_IMAP_SSL",
    "SEVEN_IMAP_USER",
    "SEVEN_EMAIL_CREDENTIAL_FILE",
    "SEVEN_MESH_ENABLED",
    "SEVEN_MESH_SECRET_FILE",
    "SEVEN_MESH_NODE_NAME",
    "SEVEN_MESH_LISTEN",
    "SEVEN_MESH_LISTEN_HOST",
    "SEVEN_MESH_LISTEN_PORT",
    "SEVEN_MESH_ADVERTISE_URL",
    "SEVEN_MESH_HUB_URL",
    "SEVEN_MESH_SYNC_SECONDS",
    "SEVEN_MESH_LAN_DISCOVERY",
    "SEVEN_MESH_LAN_GROUP",
    "SEVEN_MESH_LAN_PORT",
)


def _startup_environment(environ: dict[str, str] | None = None) -> dict[str, str]:
    source = environ if environ is not None else os.environ
    selected: dict[str, str] = {}
    for key in _STARTUP_ENV_KEYS:
        value = str(source.get(key, "")).strip()
        if not value:
            continue
        if "\x00" in value or "\r" in value or "\n" in value:
            raise ValueError(f"invalid startup environment value for {key}")
        selected[key] = value
    return selected


def _cmd_value(value: str) -> str:
    return value.replace("%", "%%").replace('"', '""')


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
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    platform_name = platform_name or sys.platform
    target = startup_target(platform_name, home)
    target.parent.mkdir(parents=True, exist_ok=True)
    python_exe = python_exe or sys.executable
    args = [python_exe, "-m", "seven", "--quiet" if quiet else "--talk"]
    startup_environment = _startup_environment(environment)
    startup_environment["SEVEN_VOICE"] = "0" if quiet else "1"
    startup_environment["SEVEN_QUIET"] = "1" if quiet else "0"
    if platform_name == "win32":
        quoted = " ".join(f'"{arg}"' if " " in arg or arg == python_exe else arg for arg in args)
        assignments = "".join(
            f'set "{key}={_cmd_value(value)}"\r\n'
            for key, value in startup_environment.items()
        )
        target.write_text(
            "@echo off\r\n" + assignments + 'start "Seven" ' + quoted + "\r\n",
            encoding="utf-8",
        )
    elif platform_name == "darwin":
        payload = {
            "Label": "ai.seven.companion",
            "ProgramArguments": args,
            "RunAtLoad": True,
            "KeepAlive": False,
            "ProcessType": "Interactive",
        }
        if startup_environment:
            payload["EnvironmentVariables"] = startup_environment
        with target.open("wb") as handle:
            plistlib.dump(payload, handle)
    else:
        environment_prefix = " ".join(
            f"{key}={shlex.quote(value)}"
            for key, value in startup_environment.items()
        )
        command = " ".join(shlex.quote(arg) for arg in args)
        if environment_prefix:
            command = f"/usr/bin/env {environment_prefix} {command}"
        target.write_text(
            "[Desktop Entry]\nType=Application\nName=Seven\n"
            f"Comment=Start Seven companion after login\nExec={command}\n"
            "Terminal=true\nX-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
        target.chmod(0o700)
    return {
        "ok": True,
        "installed": True,
        "path": str(target),
        "mode": "quiet" if quiet else "talk",
        "environment_keys": sorted(startup_environment),
    }


def remove_startup(platform_name: str | None = None, home: Path | None = None) -> dict[str, Any]:
    target = startup_target(platform_name, home)
    existed = target.exists()
    target.unlink(missing_ok=True)
    return {"ok": True, "installed": False, "removed": existed, "path": str(target)}


def startup_status(platform_name: str | None = None, home: Path | None = None) -> dict[str, Any]:
    target = startup_target(platform_name, home)
    return {"ok": True, "installed": target.exists(), "path": str(target)}
