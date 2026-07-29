"""
Browser automation — Playwright if installed, else HTTP fetch.
L4: no confirmations.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Optional


def _normalize_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        raise ValueError("url required")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    if len(value) > 8_000:
        raise ValueError("url exceeds 8000 characters")
    return value


def _profile_dir() -> Path:
    configured = os.getenv("SEVEN_BROWSER_PROFILE", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    from seven import config

    return (config.DATA_DIR / "browser_profile").resolve()


def _headless() -> bool:
    return os.getenv("SEVEN_BROWSER_HEADLESS", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _open_page(url: str, viewport: dict | None = None):
    from playwright.sync_api import sync_playwright

    profile = _profile_dir()
    profile.mkdir(parents=True, exist_ok=True)
    runtime = sync_playwright().start()
    try:
        context = runtime.chromium.launch_persistent_context(
            str(profile),
            headless=_headless(),
            viewport=viewport or {"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(
            _normalize_url(url), timeout=30_000, wait_until="domcontentloaded"
        )
        return runtime, context, page
    except Exception:
        runtime.stop()
        raise


def _close_page(runtime, context) -> None:
    try:
        context.close()
    finally:
        runtime.stop()


def browser_status() -> str:
    profile = _profile_dir()
    return json.dumps(
        {
            "ok": True,
            "playwright_installed": bool(importlib.util.find_spec("playwright")),
            "profile": str(profile),
            "profile_exists": profile.exists(),
            "headless": _headless(),
            "profile_contract": "Seven-owned isolated Chromium profile",
            "existing_chrome_profile_used": False,
        },
        indent=2,
    )


def browser_get(url: str, max_chars: int = 12000) -> str:
    """Fetch page text; try playwright, else requests/html strip via web_fetch."""
    try:
        url = _normalize_url(url)
    except ValueError as exc:
        return f"ERROR: {exc}"
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
        url = _normalize_url(url)
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


def browser_click(
    url: str,
    selector: str,
    wait_after_ms: int = 750,
) -> str:
    selector = str(selector or "").strip()
    if not selector or len(selector) > 1_000:
        return "ERROR: selector must contain 1-1000 characters"
    wait_after_ms = max(0, min(int(wait_after_ms), 10_000))
    runtime = context = None
    try:
        runtime, context, page = _open_page(url)
        locator = page.locator(selector).first
        locator.click(timeout=15_000)
        if wait_after_ms:
            page.wait_for_timeout(wait_after_ms)
        return json.dumps(
            {
                "ok": True,
                "action": "click",
                "selector": selector,
                "url": page.url,
                "title": page.title(),
            }
        )
    except ImportError:
        return "ERROR: playwright not installed. pip install 'seven-ai[browser]' && playwright install chromium"
    except Exception as exc:
        return f"ERROR browser_click: {exc}"
    finally:
        if runtime is not None and context is not None:
            _close_page(runtime, context)


def browser_fill(
    url: str,
    selector: str,
    text: str,
    submit: bool = False,
) -> str:
    selector = str(selector or "").strip()
    text = str(text or "")
    if not selector or len(selector) > 1_000:
        return "ERROR: selector must contain 1-1000 characters"
    if len(text) > 100_000:
        return "ERROR: browser text exceeds 100000 characters"
    runtime = context = None
    try:
        runtime, context, page = _open_page(url)
        locator = page.locator(selector).first
        locator.fill(text, timeout=15_000)
        if submit:
            locator.press("Enter", timeout=15_000)
            page.wait_for_timeout(750)
        return json.dumps(
            {
                "ok": True,
                "action": "fill_and_submit" if submit else "fill",
                "selector": selector,
                "characters": len(text),
                "url": page.url,
                "title": page.title(),
            }
        )
    except ImportError:
        return "ERROR: playwright not installed. pip install 'seven-ai[browser]' && playwright install chromium"
    except Exception as exc:
        return f"ERROR browser_fill: {exc}"
    finally:
        if runtime is not None and context is not None:
            _close_page(runtime, context)


def browser_extract(
    url: str,
    selector: str = "body",
    max_chars: int = 12_000,
) -> str:
    selector = str(selector or "body").strip()
    if not selector or len(selector) > 1_000:
        return "ERROR: selector must contain 1-1000 characters"
    max_chars = max(100, min(int(max_chars), 100_000))
    runtime = context = None
    try:
        runtime, context, page = _open_page(url)
        text = page.locator(selector).first.inner_text(timeout=15_000)
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars] + "\n...[truncated]"
        return (
            json.dumps(
                {
                    "ok": True,
                    "selector": selector,
                    "url": page.url,
                    "title": page.title(),
                    "truncated": truncated,
                }
            )
            + "\n\n"
            + text
        )
    except ImportError:
        return "ERROR: playwright not installed. pip install 'seven-ai[browser]' && playwright install chromium"
    except Exception as exc:
        return f"ERROR browser_extract: {exc}"
    finally:
        if runtime is not None and context is not None:
            _close_page(runtime, context)


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="browser_status",
        description="Report Seven's isolated persistent Chromium profile and Playwright readiness.",
        parameters={"type": "object", "properties": {}},
        handler=browser_status,
        tier="core",
    ))
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
    reg.register(Tool(
        name="browser_click",
        description="Open a page in Seven's isolated browser profile and click the first matching CSS or text selector.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "selector": {"type": "string"},
                "wait_after_ms": {"type": "integer", "minimum": 0, "maximum": 10000},
            },
            "required": ["url", "selector"],
        },
        handler=browser_click,
        tier="core",
    ))
    reg.register(Tool(
        name="browser_fill",
        description="Open a page in Seven's isolated browser profile, fill the first matching field, and optionally submit it.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "submit": {"type": "boolean"},
            },
            "required": ["url", "selector", "text"],
        },
        handler=browser_fill,
        tier="core",
    ))
    reg.register(Tool(
        name="browser_extract",
        description="Open a page in Seven's isolated browser profile and extract text from the first matching selector.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "selector": {"type": "string"},
                "max_chars": {"type": "integer", "minimum": 100, "maximum": 100000},
            },
            "required": ["url"],
        },
        handler=browser_extract,
        tier="core",
    ))
