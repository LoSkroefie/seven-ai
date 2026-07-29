"""Web search and fetch — real HTTP."""
from __future__ import annotations

import base64
import html as html_lib
import re
from typing import Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests


def _clean_title(value: str) -> str:
    value = re.sub(r"(?is)<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html_lib.unescape(value)).strip()


def _decode_bing_url(value: str) -> str:
    """Resolve Bing's reversible ``u=a1...`` redirect when present."""
    value = html_lib.unescape(value)
    try:
        encoded = parse_qs(urlparse(value).query).get("u", [""])[0]
        if encoded.startswith("a1"):
            payload = encoded[2:]
            payload += "=" * (-len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload).decode("utf-8")
            if decoded.startswith(("http://", "https://")):
                return decoded
    except (ValueError, UnicodeDecodeError):
        pass
    return value


def _format_results(query: str, links: list[tuple[str, str]], max_results: int) -> str:
    lines = [f"Search results for: {query}"]
    seen: set[str] = set()
    for href, title in links:
        href = unquote(html_lib.unescape(href))
        title = _clean_title(title)
        if not href or not title or href in seen:
            continue
        seen.add(href)
        lines.append(f"- {title}\n  {href}")
        if len(seen) >= max_results:
            break
    return "\n".join(lines) if len(lines) > 1 else ""


def web_search(query: str, max_results: int = 5) -> str:
    """Search public HTML endpoints without requiring an API key."""
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
        formatted = _format_results(query, links, max_results)
        if formatted:
            return formatted

        # DuckDuckGo periodically returns an HTTP 202 bot page. Bing's public
        # HTML is a bounded, no-key fallback rather than reporting false success.
        bing = requests.get(
            f"https://www.bing.com/search?q={quote_plus(query)}",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SevenAI/4.4)"},
        )
        bing.raise_for_status()
        bing_links = re.findall(
            r'<li class="b_algo".*?<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            bing.text,
            flags=re.I | re.S,
        )
        resolved = [(_decode_bing_url(href), title) for href, title in bing_links]
        formatted = _format_results(query, resolved, max_results)
        if formatted:
            return formatted
        return f"No parseable results for '{query}'. Try web_fetch on a known URL."
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
