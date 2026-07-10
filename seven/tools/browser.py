"""
Browser automation — Playwright if installed, else HTTP fetch.
L4: no confirmations.
"""
from __future__ import annotations

from typing import Optional


def browser_get(url: str, max_chars: int = 12000) -> str:
    """Fetch page text; try playwright, else requests/html strip via web_fetch."""
    if not url:
        return "ERROR: url required"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    err = ""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            text = page.inner_text("body")
            title = page.title()
            browser.close()
            if len(text) > max_chars:
                text = text[:max_chars] + "\n...[truncated]"
            return f"title={title}\nurl={url}\n\n{text}"
    except ImportError:
        err = "playwright not installed"
    except Exception as e:
        err = str(e)

    from seven.tools.web import web_fetch
    out = web_fetch(url, max_chars=max_chars)
    if err:
        return f"(playwright unavailable: {err})\n{out}"
    return out


def browser_screenshot(url: str, path: Optional[str] = None) -> str:
    try:
        from playwright.sync_api import sync_playwright
        from seven import config
        from pathlib import Path
        out = Path(path) if path else (config.DATA_DIR / "browser_shot.png")
        out = out.expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.screenshot(path=str(out), full_page=False)
            browser.close()
        return f"OK browser screenshot {out}"
    except ImportError:
        return "ERROR: playwright not installed. pip install playwright && playwright install chromium"
    except Exception as e:
        return f"ERROR browser_screenshot: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="browser_get",
        description="Load a webpage and return visible text (Playwright if available, else HTTP fetch).",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer"},
            },
            "required": ["url"],
        },
        handler=browser_get,
        tier="core",
    ))
    reg.register(Tool(
        name="browser_screenshot",
        description="Screenshot a webpage via Playwright (optional install).",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["url"],
        },
        handler=browser_screenshot,
        tier="full",
    ))
