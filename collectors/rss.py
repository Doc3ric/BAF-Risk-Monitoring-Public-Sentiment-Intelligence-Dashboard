"""Collector for public RSS feeds (Google News and relevant media).
Parses RSS feeds, extracts news coverage, and normalizes publication timestamps.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    {
        "url": "https://news.google.com/rss/search?q=%22BlockAlgo%22+OR+%22BlockAlgo+Frontier%22&hl=en-US&gl=US&ceid=US:en",
        "query": "BlockAlgo OR 'BlockAlgo Frontier'"
    },
    {
        "url": "https://news.google.com/rss/search?q=%22BAF%22+%22BlockAlgo%22&hl=en-US&gl=US&ceid=US:en",
        "query": "BAF BlockAlgo"
    }
]


class RSSNewsCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "google_news_rss",
        name: str = "Google News RSS Feed",
        feeds: Optional[List[Dict[str, str]]] = None,
        timeout: int = 15,
        user_agent: Optional[str] = None
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="rss",
            url=feeds[0]["url"] if feeds else DEFAULT_FEEDS[0]["url"],
            access_method="Public RSS feed parsing",
            requires_key=False,
            enabled=True
        )
        self.feeds = feeds or DEFAULT_FEEDS
        self.timeout = timeout
        self.user_agent = user_agent or "BAFRiskMonitor/1.0 (OSINT Research Bot; compliant; +https://github.com/local/baf-risk-monitor)"

    def _clean_summary(self, raw_summary: str) -> str:
        if not raw_summary:
            return ""
        try:
            soup = BeautifulSoup(raw_summary, "html.parser")
            return soup.get_text(strip=True)
        except Exception:
            return raw_summary

    def _parse_pub_date(self, entry: Dict[str, Any]) -> Optional[str]:
        raw_date = entry.get("published") or entry.get("updated")
        if not raw_date:
            return None
        try:
            dt = date_parser.parse(raw_date)
            return dt.isoformat()
        except Exception:
            return None

    def fetch_items(self) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        seen_urls = set()

        for feed_cfg in self.feeds:
            feed_url = feed_cfg["url"]
            try:
                # feedparser handles User-Agent and timeout via agent kwarg
                parsed = feedparser.parse(feed_url, agent=self.user_agent)
                if parsed.bozo and not parsed.entries:
                    logger.warning(f"RSS feed parsing error on {feed_url}: {parsed.bozo_exception}")
                    continue

                for entry in parsed.entries:
                    link = entry.get("link")
                    if not link or link in seen_urls:
                        continue
                    seen_urls.add(link)

                    title = entry.get("title", "News Mention")
                    summary = self._clean_summary(entry.get("summary", ""))
                    pub_date = self._parse_pub_date(entry)
                    author = entry.get("source", {}).get("title") if isinstance(entry.get("source"), dict) else entry.get("author")

                    all_items.append({
                        "title": title,
                        "url": link,
                        "content_excerpt": summary or title,
                        "published_at": pub_date,
                        "author": author or "RSS Publisher"
                    })
            except Exception as e:
                logger.warning(f"Error fetching RSS feed {feed_url}: {e}")

        return all_items
