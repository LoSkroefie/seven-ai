"""Native per-user desktop notification submission for supported platforms."""
from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Any

from seven.runtime.process import run_tracked


def notification_status(platform_name: str | None = None) -> dict[str, Any]:
    platform_name = platform_name or sys.platform
    if platform_name == "win32":
        executable = shutil.which("pwsh") or shutil.which("powershell")
        return {"available": bool(executable), "backend": "windows-toast", "executable": executable}
    if platform_name == "darwin":
        executable = shutil.which("osascript")
        return {"available": bool(executable), "backend": "macos-notification-center", "executable": executable}
    executable = shutil.which("notify-send")
    return {"available": bool(executable), "backend": "freedesktop-notify", "executable": executable}


def submit_notification(
    title: str,
    body: str,
    platform_name: str | None = None,
) -> dict[str, Any]:
    """Submit a notification. Success proves backend acceptance, not user viewing."""
    platform_name = platform_name or sys.platform
    status = notification_status(platform_name)
    if not status["available"]:
        return {**status, "ok": False, "state": "unavailable"}
    title = (title or "Seven").strip()[:120]
    body = (body or "").strip()[:1000]
    env = os.environ.copy()
    env["SEVEN_NOTIFY_TITLE"] = title
    env["SEVEN_NOTIFY_BODY"] = body
    if platform_name == "win32":
        script = (
            "$ErrorActionPreference='Stop';"
            "$t=[Security.SecurityElement]::Escape($env:SEVEN_NOTIFY_TITLE);"
            "$b=[Security.SecurityElement]::Escape($env:SEVEN_NOTIFY_BODY);"
            "$x='<toast><visual><binding template=\"ToastGeneric\"><text>'+$t+'</text><text>'+$b+'</text></binding></visual></toast>';"
            "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]>$null;"
            "[Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom,ContentType=WindowsRuntime]>$null;"
            "$d=New-Object Windows.Data.Xml.Dom.XmlDocument;$d.LoadXml($x);"
            "$n=[Windows.UI.Notifications.ToastNotification]::new($d);"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Seven').Show($n)"
        )
        command = [status["executable"], "-NoProfile", "-NonInteractive", "-Command", script]
    elif platform_name == "darwin":
        script = 'display notification (system attribute "SEVEN_NOTIFY_BODY") with title (system attribute "SEVEN_NOTIFY_TITLE")'
        command = [status["executable"], "-e", script]
    else:
        command = [status["executable"], "--app-name=Seven", title, body]
    result = run_tracked(command, env=env, timeout=15)
    ok = result.returncode == 0 and not result.timed_out
    return {
        **status,
        "ok": ok,
        "state": "submitted" if ok else "failed",
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "error": result.stderr.strip()[-1000:] if not ok else "",
    }


def notification_status_text() -> str:
    return json.dumps(notification_status(), indent=2)


def notify_desktop(title: str, body: str) -> str:
    return json.dumps(submit_notification(title, body), indent=2)
