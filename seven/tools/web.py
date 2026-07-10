"""Web search and fetch — real HTTP."""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import quote_plus

import requests


def web_search(query: str, max_results: int = 5) -> str:
    """Search via DuckDuckGo HTML (no API key)."""
    max_results = max(1, min(int(max_results), 10))
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "SevenAI/4.0 (+local-agent)"},
        )
        r.raise_for_status()
        html = r.text
        # crude parse of result links
        links = re.findall(
            r'uddg=([^&"]+).*?class="result__a"[^>]*>(.*?)</a>',
            html,
            flags=re.I | re.S,
        )
        if not links:
            # alternate pattern
            titles = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.I | re.S)
            links = [(h, t) for h, t in titles]
        from urllib.parse import unquote
        lines = [f"Search results for: {query}"]
        seen = set()
        for href, title in links:
            href = unquote(href)
            title = re.sub(r"<.*?>", "", title).strip()
            title = re.sub(r"\s+", " ", title)
            if not href or href in seen:
                continue
            seen.add(href)
            lines.append(f"- {title}\n  {href}")
            if len(seen) >= max_results:
                break
        if len(lines) == 1:
            return f"No parseable results for '{query}'. Try web_fetch on a known URL."
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR web_search: {e}"


def web_fetch(url: str, max_chars: int = 12000) -> str:
    try:
        r = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "SevenAI/4.0 (+local-agent)"},
        )
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        text = r.text
        if "html" in ctype.lower():
            # strip tags roughly
            text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
            text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
            text = re.sub(r"(?is)<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...[truncated]"
        return f"url={url}\nstatus={r.status_code}\n\n{text}"
    except Exception as e:
        return f"ERROR web_fetch: {e}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="web_search",
        description="Search the web. Returns titles and URLs.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
        handler=web_search,
    ))
    reg.register(Tool(
        name="web_fetch",
        description="Fetch a URL and return text content.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer"},
            },
            "required": ["url"],
        },
        handler=web_fetch,
    ))
