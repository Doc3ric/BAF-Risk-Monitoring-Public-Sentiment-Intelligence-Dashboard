"""Collector for official BlockAlgo Frontier (BAF) GitBook documentation and terms.
Captures snapshots, identifies policy/fee/reward changes, and records diffs.
"""

import difflib
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from database.repository import Repository
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

DEFAULT_URLS = [
    "https://baf-1.gitbook.io/baf/platform-overview/readme/introduction",
    "https://baf-1.gitbook.io/baf/"
]


class OfficialBAFCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "official_baf_docs",
        name: str = "BAF Official GitBook & Documentation",
        urls: Optional[List[str]] = None,
        timeout: int = 15,
        user_agent: Optional[str] = None
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="official",
            url=urls[0] if urls else DEFAULT_URLS[0],
            access_method="HTTP GET / GitBook Static HTML parsing",
            requires_key=False,
            enabled=True
        )
        self.urls = urls or DEFAULT_URLS
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent or "BAFRiskMonitor/1.0 (OSINT Research Bot; compliant; +https://github.com/local/baf-risk-monitor)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def fetch_items(self) -> List[Dict[str, Any]]:
        # In this specialized collector, run() handles snapshot comparison with repo
        # Here we fetch the pages and return raw representation
        items = []
        for target_url in self.urls:
            try:
                resp = requests.get(target_url, headers=self.headers, timeout=self.timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Extract title
                title_tag = soup.find("title") or soup.find("h1")
                page_title = title_tag.get_text(strip=True) if title_tag else "BAF Official Documentation"

                # Extract readable text from main body or text tags
                main_elem = soup.find("main") or soup.find("article") or soup.body
                if main_elem:
                    # Remove scripts and style elements
                    for tag in main_elem(["script", "style", "nav", "footer"]):
                        tag.decompose()
                    clean_text = "\n".join([p.get_text(strip=True) for p in main_elem.find_all(["p", "h1", "h2", "h3", "li"]) if p.get_text(strip=True)])
                else:
                    clean_text = soup.get_text(separator="\n", strip=True)

                items.append({
                    "title": f"BAF Official Documentation: {page_title}",
                    "url": target_url,
                    "content_excerpt": clean_text[:2000],
                    "raw_text": clean_text,
                    "published_at": None, # Undisclosed by GitBook; do not fabricate publication timestamp
                    "author": "BlockAlgo Frontier Team"
                })
            except Exception as e:
                logger.warning(f"Failed to fetch {target_url}: {e}")
                # Re-raise if all fail, else continue
                if len(items) == 0 and target_url == self.urls[-1]:
                    raise e
        return items

    def run(self, repo: Repository) -> Dict[str, Any]:
        """
        Custom execution for official documentation:
        Evaluates snapshot diffs in doc_snapshots alongside regular item saving.
        """
        result = super().run(repo)
        if result.get("status") == "FAILED":
            return result

        # Check snapshots and calculate diffs
        raw_items = self.fetch_items()
        for item in raw_items:
            url = item["url"]
            title = item["title"]
            raw_text = item.get("raw_text", "")
            current_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

            latest_snap = repo.get_latest_doc_snapshot(url)
            diff_summary = None
            prev_id = None

            if latest_snap:
                prev_id = latest_snap["id"]
                prev_hash = latest_snap["content_hash"]
                if prev_hash != current_hash:
                    # Content changed! Compute diff
                    old_lines = latest_snap["raw_text"].splitlines()
                    new_lines = raw_text.splitlines()
                    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm="", n=2))
                    diff_summary = "\n".join(diff[:30])
                    if len(diff) > 30:
                        diff_summary += f"\n... ({len(diff) - 30} more diff lines)"
                    logger.info(f"Documentation change detected for {url}")
                else:
                    diff_summary = "No text change detected."
            else:
                diff_summary = "Initial baseline documentation snapshot recorded."

            # Save snapshot if first time or changed
            if not latest_snap or (latest_snap and latest_snap["content_hash"] != current_hash):
                repo.save_doc_snapshot(
                    source_id=self.source_id,
                    url=url,
                    title=title,
                    content_hash=current_hash,
                    raw_text=raw_text,
                    diff_summary=diff_summary,
                    previous_snapshot_id=prev_id
                )

        return result
