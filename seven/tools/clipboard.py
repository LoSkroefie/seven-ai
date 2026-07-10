"""Clipboard access."""
from __future__ import annotations


def get_clipboard() -> str:
    try:
        import pyperclip
        data = pyperclip.paste()
        return data if data is not None else ""
    except ImportError:
        # Windows fallback
        try:
            import subprocess
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout
        except Exception as e:
            return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


def set_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"OK clipboard set ({len(text)} chars)"
    except ImportError:
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value @'\n{text}\n'@"],
                capture_output=True, text=True, timeout=10,
            )
            return f"OK clipboard set via PowerShell ({len(text)} chars)"
        except Exception as e:
            return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="get_clipboard",
        description="Read the system clipboard text.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: get_clipboard(),
    ))
    reg.register(Tool(
        name="set_clipboard",
        description="Write text to the system clipboard.",
        parameters={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        handler=set_clipboard,
    ))
