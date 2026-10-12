"""Base class for all BAF Risk Monitor source collectors.
Enforces uniform error handling, logging, idempotency, and source health tracking.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database.repository import Repository
from analysis.sentiment import analyze_sentiment
from analysis.classification import is_baf_relevant, classify_content, determine_evidence_status
from analysis.deduplication import (
    normalize_url,
    compute_content_hash,
    compute_simhash,
    find_or_create_duplicate_group
)

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    def __init__(
        self,
        source_id: str,
        name: str,
        source_type: str,
        url: Optional[str] = None,
        access_method: str = "HTTP GET",
        requires_key: bool = False,
        enabled: bool = True
    ):
        self.source_id = source_id
        self.name = name
        self.source_type = source_type
        self.url = url
        self.access_method = access_method
        self.requires_key = requires_key
        self.enabled = enabled

    def register(self, repo: Repository) -> None:
        """Register or update source in database."""
        repo.upsert_source({
            "id": self.source_id,
            "name": self.name,
            "source_type": self.source_type,
            "url": self.url,
            "access_method": self.access_method,
            "requires_key": 1 if self.requires_key else 0,
            "enabled": 1 if self.enabled else 0
        })

    @abstractmethod
    def fetch_items(self) -> List[Dict[str, Any]]:
        """
        Fetch raw items from the public source.
        Must return list of dicts with:
        title, url, content_excerpt, published_at (optional iso), author (optional)
        """
        pass

    def run(self, repo: Repository) -> Dict[str, Any]:
        """
        Execute collection pipeline:
        1. Create run record
        2. Fetch items
        3. Filter, normalize, deduplicate, classify
        4. Save items idempotently
        5. Update source status and run stats
        """
        if not self.enabled:
            logger.info(f"Source {self.name} is disabled. Skipping.")
            return {"status": "SKIPPED", "items_saved": 0}

        start_time = datetime.now(timezone.utc)
        run_id = repo.create_collection_run(self.source_id, start_time)

        try:
            raw_items = self.fetch_items()
            items_found = len(raw_items)
            items_saved = 0

            existing_items = repo.get_collected_items(limit=500)

            for raw in raw_items:
                title = raw.get("title", "").strip()
                content = raw.get("content_excerpt", "").strip()
                raw_url = raw.get("url", "").strip()
                norm_url = normalize_url(raw_url)

                # Entity relevance check (unless source is official BAF which is inherently relevant)
                if self.source_type not in ("official", "official_baf"):
                    relevant, _ = is_baf_relevant(title, content)
                    if not relevant:
                        continue

                combined_text = f"{title}. {content}"
                content_hash = compute_content_hash(combined_text)
                simhash_val = compute_simhash(combined_text)
                dup_group = find_or_create_duplicate_group(content_hash, simhash_val, existing_items)

                # Sentiment analysis
                sent_label, sent_score, sent_breakdown = analyze_sentiment(combined_text)

                # Classification
                cat_info = classify_content(title, content)
                primary_cat = cat_info["primary_category"]
                secondaries = cat_info["secondary_categories"]
                is_complaint = cat_info["is_complaint"]

                # Evidence status
                evidence_st = determine_evidence_status(
                    source_type=self.source_type,
                    primary_category=primary_cat,
                    is_complaint=is_complaint,
                    sentiment_label=sent_label
                )

                # Generate deterministic item ID
                deterministic_id = f"{self.source_id}_{content_hash[:20]}"

                item_record = {
                    "id": deterministic_id,
                    "source_id": self.source_id,
                    "url": norm_url or raw_url,
                    "title": title,
                    "content_excerpt": content[:1200],
                    "content_hash": content_hash,
                    "simhash": simhash_val,
                    "duplicate_group_id": dup_group,
                    "published_at": raw.get("published_at"),
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                    "author": raw.get("author"),
                    "sentiment_label": sent_label,
                    "sentiment_score": sent_score,
                    "primary_category": primary_cat,
                    "secondary_categories": secondaries,
                    "evidence_status": evidence_st,
                    "is_complaint": is_complaint,
                    "raw_metadata": {
                        "sentiment_scores": sent_breakdown,
                        "category_scores": cat_info.get("category_scores", {}),
                        "source_name": self.name
                    }
                }

                saved = repo.save_collected_item(item_record)
                if saved:
                    items_saved += 1
                    existing_items.append(item_record)

            final_status = "SUCCESS" if items_found > 0 else "EMPTY"
            repo.finish_collection_run(
                run_id=run_id,
                status=final_status,
                items_found=items_found,
                items_saved=items_saved
            )
            repo.update_source_status(
                source_id=self.source_id,
                status=final_status,
                error=None,
                last_run_at=start_time
            )

            return {
                "status": final_status,
                "items_found": items_found,
                "items_saved": items_saved
            }

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Collector {self.name} failed: {err_msg}", exc_info=True)
            repo.finish_collection_run(
                run_id=run_id,
                status="FAILED",
                items_found=0,
                items_saved=0,
                error_message=err_msg
            )
            repo.update_source_status(
                source_id=self.source_id,
                status="FAILED",
                error=err_msg,
                last_run_at=start_time
            )
            return {
                "status": "FAILED",
                "error": err_msg
            }
