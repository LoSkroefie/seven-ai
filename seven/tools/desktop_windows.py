"""Window awareness — list / focus windows (Windows-first)."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional


_WINDOWS_APP_ALIASES = {
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "notepad": "notepad.exe",
    "text editor": "notepad.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "control panel": "control.exe",
    "windows terminal": "wt.exe",
    "terminal": "wt.exe",
    "settings": "ms-settings:",
}


def list_windows(max_windows: int = 40) -> str:
    max_windows = max(1, min(int(max_windows or 40), 80))
    if platform.system() == "Windows":
        ps = (
            f"Get-Process | Where-Object {{$_.MainWindowTitle}} | "
            f"Select-Object -First {max_windows} Id,ProcessName,MainWindowTitle | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace",
            )
            out = (r.stdout or "").strip()
            if not out:
                return "No titled windows found."
            return out
        except Exception as e:
            return f"ERROR list_windows: {e}"
    # POSIX fallback
    try:
        r = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=10)
        return r.stdout or "wmctrl returned empty"
    except Exception as e:
        return f"ERROR: {e}"


def active_window() -> str:
    if platform.system() == "Windows":
        ps = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
}
"@
$h = [W]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 512
[void][W]::GetWindowText($h, $sb, $sb.Capacity)
$sb.ToString()
"""
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace",
            )
            title = (r.stdout or "").strip()
            return f"active_window={title or '(none)'}"
        except Exception as e:
            return f"ERROR: {e}"
    return "active_window: unsupported OS helper"


def open_url(url: str) -> str:
    import webbrowser
    if not url:
        return "ERROR: url required"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    ok = webbrowser.open(url)
    return f"OK open_url={url} launched={ok}"


@lru_cache(maxsize=128)
def _start_menu_shortcut(application: str) -> Optional[str]:
    """Find a Start Menu shortcut without invoking a shell."""
    roots = [
        Path(os.getenv("ProgramData", ""))
        / "Microsoft/Windows/Start Menu/Programs",
        Path(os.getenv("APPDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs",
    ]
    needle = application.casefold().strip()
    exact = []
    partial = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            shortcuts = root.rglob("*.lnk")
            for shortcut in shortcuts:
                stem = shortcut.stem.casefold()
                if stem == needle:
                    exact.append(shortcut)
                elif needle in stem:
                    partial.append(shortcut)
        except OSError:
            continue
    matches = exact or partial
    if not matches:
        return None
    return str(sorted(matches, key=lambda item: (len(item.stem), str(item)))[0])


def open_app(application: str) -> str:
    """Launch a desktop application and return an auditable result."""
    requested = str(application or "").strip().strip('"\'')
    requested = requested.removeprefix("the ").strip()
    if not requested:
        return "ERROR: application is required"
    if platform.system() != "Windows":
        return "ERROR: open_app currently supports Windows only"
    if requested.casefold().startswith(("http://", "https://")):
        return "ERROR: use open_url for web addresses"

    target = _WINDOWS_APP_ALIASES.get(requested.casefold())
    if target is None:
        candidate = Path(requested).expanduser()
        if candidate.exists():
            target = str(candidate.resolve())
        else:
            target = shutil.which(requested) or _start_menu_shortcut(requested)
    if not target:
        return f"ERROR: application not found: {requested}"

    try:
        if target.endswith(":") or target.casefold().endswith(".lnk"):
            os.startfile(target)  # type: ignore[attr-defined]
            pid = None
        else:
            process = subprocess.Popen(
                [target],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            pid = int(process.pid)
    except Exception as exc:
        return f"ERROR open_app {requested}: {exc}"

    return json.dumps(
        {
            "ok": True,
            "application": requested,
            "target": target,
            "launched": True,
            "pid": pid,
        },
        ensure_ascii=False,
    )


def focus_window(title_substr: str) -> str:
    """Focus first window whose title contains title_substr (Windows)."""
    if not title_substr:
        return "ERROR: title_substr required"
    if platform.system() != "Windows":
        return "ERROR: focus_window currently Windows-only"
    # Escape single quotes for PowerShell
    sub = title_substr.replace("'", "''")
    ps = f"""
$p = Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{sub}*' }} | Select-Object -First 1
if (-not $p) {{ Write-Output 'ERROR: no window match'; exit 0 }}
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class F {{
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
[void][F]::ShowWindow($p.MainWindowHandle, 9)
[void][F]::SetForegroundWindow($p.MainWindowHandle)
Write-Output ("OK focused pid=" + $p.Id + " title=" + $p.MainWindowTitle)
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
        return (r.stdout or r.stderr or "done").strip()
    except Exception as e:
        return f"ERROR focus_window: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="list_windows",
        description="List open desktop windows (pid, process, title).",
        parameters={
            "type": "object",
            "properties": {"max_windows": {"type": "integer"}},
        },
        handler=list_windows,
        tier="core",
    ))
    reg.register(Tool(
        name="active_window",
        description="Get the foreground window title.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: active_window(),
        tier="core",
    ))
    reg.register(Tool(
        name="open_url",
        description="Open a URL in the default browser.",
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        handler=open_url,
        tier="core",
    ))
    reg.register(Tool(
        name="open_app",
        description=(
            "Launch a Windows desktop application by common name, executable, "
            "path, or Start Menu shortcut. Use this before claiming an app opened."
        ),
        parameters={
            "type": "object",
            "properties": {
                "application": {
                    "type": "string",
                    "description": "Application name such as calculator or notepad",
                }
            },
            "required": ["application"],
        },
        handler=open_app,
        tier="core",
    ))
    reg.register(Tool(
        name="focus_window",
        description="Bring a desktop window to the foreground by partial title match.",
        parameters={
            "type": "object",
            "properties": {
                "title_substr": {"type": "string", "description": "Substring of window title"},
            },
            "required": ["title_substr"],
        },
        handler=focus_window,
        tier="core",
    ))
