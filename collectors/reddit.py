"""Collector for public Reddit discussions and forum posts.
Uses public Reddit search JSON with rate-limiting respect and compliant User-Agent headers.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"


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
            access_method="Public Reddit JSON Search API",
            requires_key=False,
            enabled=True
        )
        self.queries = queries or ["BlockAlgo", "BlockAlgo Frontier"]
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent or "BAFRiskMonitor/1.0 (OSINT Research Bot; compliant; +https://github.com/local/baf-risk-monitor)",
            "Accept": "application/json"
        }

    def fetch_items(self) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        seen_urls = set()

        for q in self.queries:
            params = {
                "q": q,
                "sort": "new",
                "limit": 25,
                "type": "link"
            }
            try:
                resp = requests.get(REDDIT_SEARCH_URL, params=params, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 429:
                    logger.warning("Reddit API returned 429 Too Many Requests (rate-limited). Skipping query.")
                    break
                elif resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for post in children:
                        post_data = post.get("data", {})
                        permalink = post_data.get("permalink")
                        if not permalink:
                            continue
                        full_url = f"https://www.reddit.com{permalink}"
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        title = post_data.get("title", "Reddit Discussion")
                        selftext = post_data.get("selftext", "")
                        created_utc = post_data.get("created_utc")
                        pub_date = None
                        if created_utc:
                            pub_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

                        author = post_data.get("author", "[deleted]")
                        subreddit = post_data.get("subreddit_name_prefixed", "r/reddit")

                        excerpt = f"[{subreddit}] {selftext[:800]}" if selftext else f"[{subreddit}] {title}"

                        all_items.append({
                            "title": title,
                            "url": full_url,
                            "content_excerpt": excerpt,
                            "published_at": pub_date,
                            "author": f"u/{author}"
                        })
                else:
                    logger.warning(f"Reddit search returned status {resp.status_code} for query {q}")
            except Exception as e:
                logger.warning(f"Error querying Reddit for {q}: {e}")

        return all_items
