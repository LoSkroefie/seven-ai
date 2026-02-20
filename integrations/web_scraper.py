"""
Seven AI — Web Page Scraper

Extracts readable content from web pages using requests + BeautifulSoup.
Complements Seven's existing web search by actually reading page content.

Inspired by PentAGI's isolated browser scraper, but lightweight and local.

Usage:
    from integrations.web_scraper import WebScraper

    scraper = WebScraper()
    page = scraper.read_page("https://example.com")
    print(page['title'])
    print(page['text'][:500])

    # Summarize for context injection
    summary = scraper.extract_for_context("https://en.wikipedia.org/wiki/Python")
"""

import logging
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class WebScraper:
    """Lightweight web page content extractor"""

    DEFAULT_HEADERS = {
        'User-Agent': 'Seven-AI/3.2 (Local AI Companion; +https://github.com/LoSkroefie/seven-ai)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    # Tags to remove entirely (not just their text)
    REMOVE_TAGS = ['script', 'style', 'nav', 'footer', 'header', 'aside',
                   'noscript', 'iframe', 'svg', 'form']

    # Tags that indicate main content
    CONTENT_TAGS = ['article', 'main', '[role="main"]']

    def __init__(self, timeout: int = 15, max_content_length: int = 500_000,
                 logger: Optional[logging.Logger] = None):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.logger = logger or logging.getLogger("WebScraper")
        self._session = requests.Session() if HAS_REQUESTS else None
        if self._session:
            self._session.headers.update(self.DEFAULT_HEADERS)

    def read_page(self, url: str) -> Dict:
        """
        Fetch and extract readable content from a URL.

        Returns dict with:
            title, text, links, meta_description, word_count, url, success, error
        """
        result = {
            'url': url,
            'title': '',
            'text': '',
            'links': [],
            'meta_description': '',
            'word_count': 0,
            'success': False,
            'error': None,
        }

        if not HAS_REQUESTS:
            result['error'] = "requests library not installed"
            return result

        if not HAS_BS4:
            result['error'] = "beautifulsoup4 not installed (pip install beautifulsoup4)"
            return result

        try:
            resp = self._session.get(url, timeout=self.timeout,
                                      allow_redirects=True)
            resp.raise_for_status()

            if len(resp.content) > self.max_content_length:
                result['error'] = f"Page too large ({len(resp.content)} bytes)"
                return result

            content_type = resp.headers.get('content-type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                result['error'] = f"Not HTML: {content_type}"
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Title
            title_tag = soup.find('title')
            result['title'] = title_tag.get_text(strip=True) if title_tag else ''

            # Meta description
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta:
                result['meta_description'] = meta.get('content', '')[:500]

            # Remove unwanted tags
            for tag_name in self.REMOVE_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # Try to find main content area first
            main_content = None
            for selector in self.CONTENT_TAGS:
                if selector.startswith('['):
                    main_content = soup.select_one(selector)
                else:
                    main_content = soup.find(selector)
                if main_content:
                    break

            # Fall back to body
            content_root = main_content or soup.find('body') or soup

            # Extract text
            text = content_root.get_text(separator='\n', strip=True)
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            result['text'] = text.strip()
            result['word_count'] = len(text.split())

            # Extract links
            base_url = resp.url
            links = []
            for a in content_root.find_all('a', href=True)[:50]:
                href = a['href']
                if href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                absolute = urljoin(base_url, href)
                link_text = a.get_text(strip=True)[:100]
                if link_text:
                    links.append({'text': link_text, 'url': absolute})
            result['links'] = links

            result['success'] = True

        except requests.exceptions.Timeout:
            result['error'] = f"Timeout after {self.timeout}s"
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection failed"
        except requests.exceptions.HTTPError as e:
            result['error'] = f"HTTP {e.response.status_code}"
        except Exception as e:
            result['error'] = str(e)[:200]

        return result

    def extract_for_context(self, url: str, max_chars: int = 2000) -> str:
        """
        Extract page content formatted for LLM context injection.

        Returns a concise text summary suitable for prompt inclusion.
        """
        page = self.read_page(url)

        if not page['success']:
            return f"[Could not read {url}: {page['error']}]"

        parts = []
        if page['title']:
            parts.append(f"Title: {page['title']}")
        if page['meta_description']:
            parts.append(f"Summary: {page['meta_description']}")

        text = page['text']
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"
        parts.append(f"\nContent:\n{text}")

        return "\n".join(parts)

    def search_page(self, url: str, query: str) -> List[str]:
        """
        Search a page for relevant paragraphs matching a query.

        Returns list of matching paragraph texts.
        """
        page = self.read_page(url)
        if not page['success']:
            return []

        query_words = set(query.lower().split())
        paragraphs = page['text'].split('\n\n')

        scored = []
        for para in paragraphs:
            if len(para.strip()) < 20:
                continue
            para_words = set(para.lower().split())
            overlap = len(query_words & para_words)
            if overlap > 0:
                scored.append((overlap, para.strip()))

        scored.sort(key=lambda x: -x[0])
        return [text for _, text in scored[:5]]
