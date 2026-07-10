"""Screen capture + optional mouse/keyboard control."""
from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional

from seven import config


def screenshot(path: Optional[str] = None, region: Optional[str] = None) -> str:
    """
    Capture screen. Saves PNG and returns path + size.
    region: optional "x,y,w,h"
    """
    try:
        import pyautogui
    except ImportError:
        return "ERROR: pyautogui not installed. pip install pyautogui pillow"
    out = Path(path) if path else (config.DATA_DIR / "last_screenshot.png")
    out = out.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if region:
        try:
            x, y, w, h = [int(v.strip()) for v in region.split(",")]
            kwargs["region"] = (x, y, w, h)
        except Exception as e:
            return f"ERROR parsing region (want x,y,w,h): {e}"
    img = pyautogui.screenshot(**kwargs)
    img.save(str(out))
    return f"OK screenshot saved to {out.resolve()} size={img.size}"


def screenshot_b64() -> str:
    try:
        import pyautogui
        from PIL import Image
    except ImportError:
        return ""
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.click(x=int(x), y=int(y), clicks=int(clicks), button=button)
        return f"OK clicked {button} at ({x},{y}) x{clicks}"
    except Exception as e:
        return f"ERROR: {e}"


def mouse_move(x: int, y: int) -> str:
    try:
        import pyautogui
        pyautogui.moveTo(int(x), int(y))
        return f"OK moved mouse to ({x},{y})"
    except Exception as e:
        return f"ERROR: {e}"


def type_text(text: str, interval: float = 0.02) -> str:
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=interval) if text.isascii() else None
        if not text.isascii():
            # pyautogui.typewrite is ASCII-only; use clipboard paste fallback
            try:
                import pyperclip
                old = None
                try:
                    old = pyperclip.paste()
                except Exception:
                    pass
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
                if old is not None:
                    pyperclip.copy(old)
            except ImportError:
                return "ERROR: non-ASCII typing needs pyperclip. pip install pyperclip"
        return f"OK typed {len(text)} chars"
    except Exception as e:
        return f"ERROR: {e}"


def hotkey(keys: str) -> str:
    """keys: comma-separated e.g. 'ctrl,c' or 'alt,tab'"""
    try:
        import pyautogui
        parts = [k.strip() for k in keys.split(",") if k.strip()]
        pyautogui.hotkey(*parts)
        return f"OK hotkey {parts}"
    except Exception as e:
        return f"ERROR: {e}"


def screen_size() -> str:
    try:
        import pyautogui
        w, h = pyautogui.size()
        x, y = pyautogui.position()
        return f"screen={w}x{h} mouse=({x},{y})"
    except Exception as e:
        return f"ERROR: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="screenshot",
        description="Capture the screen to a PNG file. Returns path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "region": {"type": "string", "description": "Optional x,y,w,h"},
            },
        },
        handler=screenshot,
    ))
    reg.register(Tool(
        name="screen_size",
        description="Get screen resolution and mouse position.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: screen_size(),
    ))
    reg.register(Tool(
        name="mouse_click",
        description="Click mouse at screen coordinates. FAILSAFE: move mouse to corner to abort.",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"]},
                "clicks": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
        handler=mouse_click,
    ))
    reg.register(Tool(
        name="mouse_move",
        description="Move mouse cursor to coordinates.",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
        handler=mouse_move,
    ))
    reg.register(Tool(
        name="type_text",
        description="Type text via keyboard into the focused window.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "interval": {"type": "number"},
            },
            "required": ["text"],
        },
        handler=type_text,
    ))
    reg.register(Tool(
        name="hotkey",
        description="Press a key combination. keys is comma-separated, e.g. 'ctrl,s' or 'alt,tab'.",
        parameters={
            "type": "object",
            "properties": {
                "keys": {"type": "string"},
            },
            "required": ["keys"],
        },
        handler=hotkey,
    ))
