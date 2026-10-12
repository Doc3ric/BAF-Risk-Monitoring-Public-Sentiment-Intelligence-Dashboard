"""Collector for GDELT Global News Intelligence API.
Monitors public news mentions of BlockAlgo / BAF across international press.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from dateutil import parser as date_parser

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


class GDELTCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "gdelt_news",
        name: str = "GDELT Global News Intelligence API",
        queries: Optional[List[str]] = None,
        timeout: int = 15,
        user_agent: Optional[str] = None
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="news",
            url=GDELT_ENDPOINT,
            access_method="Public GDELT 2.0 DOC API (JSON)",
            requires_key=False,
            enabled=True
        )
        self.queries = queries or ['"BlockAlgo"', '"BlockAlgo Frontier"']
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent or "BAFRiskMonitor/1.0 (OSINT Research Bot; compliant; +https://github.com/local/baf-risk-monitor)",
            "Accept": "application/json"
        }

    def _parse_gdelt_date(self, seendate_str: Optional[str]) -> Optional[str]:
        if not seendate_str:
            return None
        try:
            # Format: YYYYMMDDTHHMMSSZ
            clean = seendate_str.replace("Z", "")
            dt = datetime.strptime(clean, "%Y%m%dT%H%M%S")
            return dt.isoformat()
        except Exception:
            try:
                dt = date_parser.parse(seendate_str)
                return dt.isoformat()
            except Exception:
                return None

    def fetch_items(self) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        seen_urls = set()

        for q in self.queries:
            params = {
                "query": q,
                "mode": "artlist",
                "format": "json",
                "maxrecords": 50,
                "sort": "datedesc"
            }
            try:
                resp = requests.get(GDELT_ENDPOINT, params=params, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    text_resp = resp.text.strip()
                    if not text_resp or text_resp == "{}":
                        continue
                    data = resp.json()
                    articles = data.get("articles", [])
                    for art in articles:
                        art_url = art.get("url")
                        if not art_url or art_url in seen_urls:
                            continue
                        seen_urls.add(art_url)
                        pub_date = self._parse_gdelt_date(art.get("seendate"))
                        all_items.append({
                            "title": art.get("title", "GDELT News Observation"),
                            "url": art_url,
                            "content_excerpt": f"Source: {art.get('domain', '')} ({art.get('sourcecountry', 'Unknown')}). Mention of {q}",
                            "published_at": pub_date,
                            "author": art.get("domain")
                        })
                else:
                    logger.warning(f"GDELT returned status code {resp.status_code} for query {q}")
            except Exception as e:
                logger.warning(f"GDELT request error for query {q}: {e}")

        return all_items
