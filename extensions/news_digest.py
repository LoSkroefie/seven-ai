"""
News Digest Extension — Seven AI

Reads configurable RSS feeds and presents headlines.
Can provide news context when users ask about current events.
"""

import logging
from datetime import datetime
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("NewsDigest")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Default RSS feeds (user can override via config)
DEFAULT_FEEDS = {
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters Top": "https://feeds.reuters.com/reuters/topNews",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Hacker News": "https://hnrss.org/frontpage",
}


class NewsDigestExtension(SevenExtension):
    """Fetch and summarize news headlines from RSS feeds"""

    name = "News Digest"
    version = "1.0"
    description = "Fetches news from RSS feeds and summarizes headlines"
    author = "Seven AI"

    schedule_interval_minutes = 240  # Every 4 hours
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.feeds = {}
        self.last_headlines = []
        self.last_fetch = None

        # Try to get feeds from config, fallback to defaults
        try:
            import config
            self.feeds = getattr(config, 'NEWS_RSS_FEEDS', DEFAULT_FEEDS)
        except ImportError:
            self.feeds = DEFAULT_FEEDS

    def run(self, context: dict = None) -> dict:
        if not HAS_FEEDPARSER and not HAS_REQUESTS:
            return {"message": "feedparser or requests not installed", "status": "unavailable"}

        all_headlines = []

        for source_name, feed_url in self.feeds.items():
            try:
                entries = self._fetch_feed(feed_url)
                for entry in entries[:5]:  # Top 5 per source
                    all_headlines.append({
                        "source": source_name,
                        "title": entry.get("title", "Untitled"),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                    })
            except Exception as e:
                logger.warning(f"[News] Failed to fetch {source_name}: {e}")

        if not all_headlines:
            return {"message": "No news headlines available.", "status": "empty"}

        self.last_headlines = all_headlines[:20]
        self.last_fetch = datetime.now().isoformat()

        # Build readable digest
        digest_parts = [f"News Digest — {datetime.now().strftime('%B %d, %Y %H:%M')}"]
        current_source = None
        for item in self.last_headlines:
            if item["source"] != current_source:
                current_source = item["source"]
                digest_parts.append(f"\n[{current_source}]")
            digest_parts.append(f"  - {item['title']}")

        digest = "\n".join(digest_parts)
        logger.info(f"[News] Fetched {len(all_headlines)} headlines from {len(self.feeds)} feeds")

        return {
            "message": digest,
            "headlines": self.last_headlines,
            "sources": len(self.feeds),
            "status": "ok",
        }

    def _fetch_feed(self, url: str) -> list:
        """Fetch RSS feed entries"""
        if HAS_FEEDPARSER:
            feed = feedparser.parse(url)
            return feed.entries[:5]

        # Fallback: basic XML parsing with requests
        if HAS_REQUESTS:
            import xml.etree.ElementTree as ET
            resp = requests.get(url, timeout=10, headers={"User-Agent": "SevenAI/1.0"})
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            entries = []
            # RSS 2.0 format
            for item in root.findall('.//item')[:5]:
                entries.append({
                    "title": item.findtext("title", "Untitled"),
                    "link": item.findtext("link", ""),
                    "published": item.findtext("pubDate", ""),
                })
            # Atom format
            if not entries:
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in root.findall('.//atom:entry', ns)[:5]:
                    entries.append({
                        "title": entry.findtext("atom:title", "Untitled", ns),
                        "link": entry.find("atom:link", ns).get("href", "") if entry.find("atom:link", ns) is not None else "",
                        "published": entry.findtext("atom:published", "", ns),
                    })
            return entries

        return []

    def on_message(self, user_message: str, bot_response: str):
        """Provide news context when relevant"""
        lower = user_message.lower()
        news_words = ["news", "headlines", "what's happening", "current events",
                      "latest news", "any news", "tell me the news"]
        if any(w in lower for w in news_words) and self.last_headlines:
            top3 = self.last_headlines[:3]
            lines = ["Here are the latest headlines:"]
            for h in top3:
                lines.append(f"  - [{h['source']}] {h['title']}")
            return "\n".join(lines)
        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "feeds_configured": len(self.feeds),
            "headlines_cached": len(self.last_headlines),
            "last_fetch": self.last_fetch,
            "running": True,
        }
