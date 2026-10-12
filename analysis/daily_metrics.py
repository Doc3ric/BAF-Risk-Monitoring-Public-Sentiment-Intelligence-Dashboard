"""Daily metrics aggregation engine for BAF Risk Monitor.
Normalizes timestamps to Asia/Manila timezone and aggregates indicators without fabricating zero-complaint assumptions.
"""

from datetime import datetime, timezone
import zoneinfo
from typing import Dict, Any, List, Optional
from database.repository import Repository
from analysis.risk_rules import evaluate_risk_posture

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def to_manila_date(ts_str: Optional[str]) -> str:
    """Convert an ISO timestamp string to YYYY-MM-DD in Asia/Manila."""
    if not ts_str:
        return datetime.now(MANILA_TZ).strftime("%Y-%m-%d")
    try:
        # Handle trailing Z or offset
        clean_ts = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        manila_dt = dt.astimezone(MANILA_TZ)
        return manila_dt.strftime("%Y-%m-%d")
    except Exception:
        return ts_str[:10]


def compute_daily_metrics_for_date(
    repo: Repository,
    target_date: str,
    thresholds: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute daily metrics for a given date (YYYY-MM-DD in Asia/Manila).
    """
    items = repo.get_collected_items(start_date=target_date, end_date=target_date, limit=10000)
    sources = repo.get_sources()
    snapshots = repo.get_doc_snapshots(limit=100)

    # Filter doc changes for target date
    day_snapshots = [
        s for s in snapshots
        if to_manila_date(s.get("snapshot_timestamp")) == target_date
        and s.get("diff_summary") and s.get("diff_summary") != "No text change detected."
    ]

    # Exclude company self-published documentation from public sentiment counters
    public_items = [i for i in items if i.get("evidence_status") != "OFFICIAL_STATEMENT"]

    total_items = len(items)
    positive_count = sum(1 for i in public_items if i.get("sentiment_label") == "POSITIVE")
    negative_count = sum(1 for i in public_items if i.get("sentiment_label") == "NEGATIVE")
    neutral_count = sum(1 for i in public_items if i.get("sentiment_label") == "NEUTRAL")
    mixed_count = sum(1 for i in public_items if i.get("sentiment_label") == "MIXED")
    complaints = sum(1 for i in items if i.get("is_complaint"))
    corroborated = sum(1 for i in items if i.get("evidence_status") == "CORROBORATED")

    active_sources = sum(1 for s in sources if s.get("enabled", 1))
    failed_sources = sum(1 for s in sources if s.get("enabled", 1) and s.get("last_status") == "FAILED")

    # Evaluate risk posture
    posture, alerts = evaluate_risk_posture(items, sources, day_snapshots, thresholds or {})

    metrics = {
        "date": target_date,
        "total_items_collected": total_items,
        "positive_mentions": positive_count,
        "negative_mentions": negative_count,
        "neutral_mentions": neutral_count,
        "mixed_mentions": mixed_count,
        "complaint_volume": complaints,
        "corroborated_events": corroborated,
        "doc_changes_detected": len(day_snapshots),
        "active_sources_count": active_sources,
        "failed_sources_count": failed_sources,
        "monitoring_state": posture
    }

    repo.save_or_update_daily_metrics(target_date, metrics)
    return metrics
