"""Window awareness — list / focus windows (Windows-first)."""
from __future__ import annotations

import platform
import subprocess
from typing import Optional


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
