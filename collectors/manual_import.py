"""Collector and ingestion engine for manual intelligence entry, regulatory uploads, and CSV/JSON imports.
Enables monitoring of sources without automated APIs (e.g., SEC Philippines advisories, corporate registries).
"""

import csv
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database.repository import Repository
from collectors.base import BaseCollector
from analysis.sentiment import analyze_sentiment
from analysis.classification import classify_content, determine_evidence_status
from analysis.deduplication import (
    normalize_url,
    compute_content_hash,
    compute_simhash,
    find_or_create_duplicate_group
)

logger = logging.getLogger(__name__)


class ManualImportCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "manual_import",
        name: str = "Manual Intelligence & Regulatory Uploads"
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="manual",
            url=None,
            access_method="Direct User Entry / CSV / JSON file import",
            requires_key=False,
            enabled=True
        )

    def fetch_items(self) -> List[Dict[str, Any]]:
        # Manual collector ingests via import_single_item or import_file
        return []

    def import_single_item(
        self,
        repo: Repository,
        title: str,
        url: str,
        content: str,
        source_label: str = "Manual Investigation",
        published_at: Optional[str] = None,
        author: Optional[str] = None,
        forced_category: Optional[str] = None,
        forced_evidence_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually ingest a single verified finding or regulatory advisory.
        """
        start_time = datetime.now(timezone.utc)
        clean_url = normalize_url(url)
        combined_text = f"{title}. {content}"
        content_hash = compute_content_hash(combined_text)
        simhash_val = compute_simhash(combined_text)

        existing_items = repo.get_collected_items(limit=500)
        dup_group = find_or_create_duplicate_group(content_hash, simhash_val, existing_items)

        sent_label, sent_score, sent_breakdown = analyze_sentiment(combined_text)
        cat_info = classify_content(title, content)

        primary_cat = forced_category or cat_info["primary_category"]
        evidence_st = forced_evidence_status or determine_evidence_status(
            source_type="manual",
            primary_category=primary_cat,
            is_complaint=cat_info["is_complaint"],
            sentiment_label=sent_label
        )

        item_id = f"manual_{content_hash[:20]}"
        item_record = {
            "id": item_id,
            "source_id": self.source_id,
            "url": clean_url or url,
            "title": title,
            "content_excerpt": content[:1200],
            "content_hash": content_hash,
            "simhash": simhash_val,
            "duplicate_group_id": dup_group,
            "published_at": published_at or start_time.isoformat(),
            "collected_at": start_time.isoformat(),
            "author": author or source_label,
            "sentiment_label": sent_label,
            "sentiment_score": sent_score,
            "primary_category": primary_cat,
            "secondary_categories": cat_info["secondary_categories"],
            "evidence_status": evidence_st,
            "is_complaint": cat_info["is_complaint"],
            "raw_metadata": {
                "source_label": source_label,
                "imported_manually": True,
                "category_scores": cat_info.get("category_scores", {})
            }
        }

        saved = repo.save_collected_item(item_record)
        repo.update_source_status(self.source_id, "SUCCESS", None, start_time)
        return {"status": "SUCCESS" if saved else "DUPLICATE", "item_id": item_id, "saved": saved}

    def import_from_csv(self, repo: Repository, csv_content: str) -> Dict[str, Any]:
        """Import rows from CSV text containing headers: title, url, content, source, published_at, category"""
        reader = csv.DictReader(csv_content.splitlines())
        saved_count = 0
        total_rows = 0

        for row in reader:
            total_rows += 1
            title = row.get("title", "").strip()
            url = row.get("url", "").strip()
            content = row.get("content", row.get("excerpt", "")).strip()
            if not title:
                continue

            res = self.import_single_item(
                repo=repo,
                title=title,
                url=url,
                content=content,
                source_label=row.get("source", "CSV Import"),
                published_at=row.get("published_at"),
                author=row.get("author"),
                forced_category=row.get("category"),
                forced_evidence_status=row.get("evidence_status")
            )
            if res.get("saved"):
                saved_count += 1

        return {"total_rows": total_rows, "saved_count": saved_count}
