"""Collector for public Reddit discussions, scam investigations, and forum posts.
Uses public Reddit search feeds across investigative subreddits (r/ScammersPH, r/phinvest, r/Scams)
with rate-limit handling and compliant XML/RSS parsing.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = ["ScammersPH", "phinvest", "Scams", "CryptoScams"]


class RedditCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "reddit_discussions",
        name: str = "Reddit Public Discussions & Forums",
        queries: Optional[List[str]] = None,
        timeout: int = 15,
        user_agent: Optional[str] = None
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="social",
            url="https://www.reddit.com",
            access_method="Public Reddit Search & Subreddit RSS Feeds",
            requires_key=False,
            enabled=True
        )
        self.queries = queries or ["BlockAlgo", "BlockAlgo Frontier", "baf9.ai"]
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _clean_summary(self, raw_html: str) -> str:
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return raw_html

    def fetch_items(self) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        seen_urls = set()

        for q in self.queries:
            # 1. Search across specific scam/investigative subreddits
            for sub in TARGET_SUBREDDITS:
                rss_url = f"https://www.reddit.com/r/{sub}/search.rss?q={q}&restrict_sr=1"
                try:
                    resp = requests.get(rss_url, headers=self.headers, timeout=self.timeout)
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries:
                            link = entry.get("link")
                            if not link or link in seen_urls:
                                continue
                            seen_urls.add(link)

                            title = entry.get("title", f"Reddit r/{sub} Post")
                            summary = self._clean_summary(entry.get("summary", ""))
                            raw_pub = entry.get("published") or entry.get("updated")
                            pub_date = None
                            if raw_pub:
                                try:
                                    dt = date_parser.parse(raw_pub)
                                    pub_date = dt.astimezone(timezone.utc).isoformat()
                                except Exception:
                                    pub_date = raw_pub

                            author = entry.get("author", f"r/{sub} user")
                            excerpt = f"[r/{sub}] {title}. {summary[:600]}"

                            all_items.append({
                                "title": title,
                                "url": link,
                                "content_excerpt": excerpt,
                                "published_at": pub_date,
                                "author": author
                            })
                    elif resp.status_code == 429:
                        logger.warning(f"Reddit rate-limited (429) for r/{sub}. Pausing.")
                        break
                    else:
                        logger.info(f"Reddit r/{sub} returned HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Error fetching Reddit RSS for r/{sub}: {e}")

            # 2. General site-wide search fallback
            global_rss = f"https://www.reddit.com/search.rss?q={q}&sort=new"
            try:
                resp = requests.get(global_rss, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        link = entry.get("link")
                        if not link or link in seen_urls:
                            continue
                        seen_urls.add(link)

                        title = entry.get("title", "Reddit Discussion")
                        summary = self._clean_summary(entry.get("summary", ""))
                        raw_pub = entry.get("published") or entry.get("updated")
                        pub_date = None
                        if raw_pub:
                            try:
                                dt = date_parser.parse(raw_pub)
                                pub_date = dt.astimezone(timezone.utc).isoformat()
                            except Exception:
                                pub_date = raw_pub

                        author = entry.get("author", "Reddit user")
                        all_items.append({
                            "title": title,
                            "url": link,
                            "content_excerpt": f"{title}. {summary[:600]}",
                            "published_at": pub_date,
                            "author": author
                        })
            except Exception as e:
                logger.warning(f"Error fetching global Reddit RSS: {e}")

        return all_items
