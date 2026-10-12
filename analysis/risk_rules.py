"""Configurable Risk Alert rules engine.
Generates evidence-backed posture assessments across three monitoring states:
NORMAL, INCREASED_CONCERN, SERIOUS_WARNING.
Never produces a black-box percentage or automated investment recommendation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple


def evaluate_risk_posture(
    collected_items: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    doc_changes: List[Dict[str, Any]],
    thresholds: Dict[str, Any]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Evaluate system risk posture and generate specific alerts.
    Returns:
        (posture_state, active_alerts)
    where posture_state is 'NORMAL', 'INCREASED_CONCERN', or 'SERIOUS_WARNING'.
    """
    alerts: List[Dict[str, Any]] = []

    withdrawal_threshold = thresholds.get("withdrawal_complaints_threshold", 3)
    deposit_threshold = thresholds.get("deposit_problems_threshold", 3)
    stale_hours_threshold = thresholds.get("source_stale_hours_threshold", 48)

    now = datetime.now(timezone.utc)
    recent_48h = now - timedelta(hours=48)
    recent_7d = now - timedelta(days=7)

    # -------------------------------------------------------------
    # 1. Check Source Health & Data Freshness
    # -------------------------------------------------------------
    failing_sources = []
    stale_sources = []
    for s in sources:
        if not s.get("enabled", 1):
            continue
        status = s.get("last_status", "PENDING")
        last_run = s.get("last_run_at")

        if status == "FAILED":
            failing_sources.append(s["name"])

        if last_run:
            try:
                lr_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00")).replace(tzinfo=None)
                if (now - lr_dt).total_seconds() > (stale_hours_threshold * 3600):
                    stale_sources.append(f"{s['name']} (stale for >{stale_hours_threshold}h)")
            except Exception:
                pass

    if failing_sources:
        alerts.append({
            "alert_level": "INCREASED_CONCERN",
            "rule_name": "SOURCE_COLLECTION_FAILURE",
            "title": "Data Collector Failure Detected",
            "description": f"Collection failed for {len(failing_sources)} monitored source(s). Data completeness may be impaired.",
            "evidence_summary": f"Failing sources: {', '.join(failing_sources)}. Verify connector configurations or network reachability."
        })

    if stale_sources:
        alerts.append({
            "alert_level": "INCREASED_CONCERN",
            "rule_name": "SOURCE_DATA_STALE",
            "title": "Stale Intelligence Sources",
            "description": f"{len(stale_sources)} source(s) have not updated within {stale_hours_threshold} hours.",
            "evidence_summary": f"Sources: {', '.join(stale_sources)}."
        })

    # -------------------------------------------------------------
    # 2. Check Withdrawal Complaints Spike (Unique clusters)
    # -------------------------------------------------------------
    withdrawal_items = [
        item for item in collected_items
        if item.get("primary_category") == "withdrawal_issues"
    ]
    # Deduplicate by duplicate_group_id or content_hash
    unique_withdrawal_groups = set()
    withdrawal_evidence_titles = []
    for item in withdrawal_items:
        group_id = item.get("duplicate_group_id") or item.get("content_hash") or item.get("id")
        if group_id not in unique_withdrawal_groups:
            unique_withdrawal_groups.add(group_id)
            withdrawal_evidence_titles.append(f"[{item.get('source_name', 'Source')}] {item.get('title', '')[:80]}")

    if len(unique_withdrawal_groups) >= withdrawal_threshold:
        alerts.append({
            "alert_level": "SERIOUS_WARNING",
            "rule_name": "WITHDRAWAL_COMPLAINTS_SPIKE",
            "title": "Critical Surge in Withdrawal Complaints",
            "description": f"Detected {len(unique_withdrawal_groups)} unique, uncorroborated or reported withdrawal failure complaints, meeting or exceeding threshold ({withdrawal_threshold}).",
            "evidence_summary": f"Recent complaints: {'; '.join(withdrawal_evidence_titles[:4])}"
        })

    # -------------------------------------------------------------
    # 3. Check Deposit & Payment Failures
    # -------------------------------------------------------------
    deposit_items = [
        item for item in collected_items
        if item.get("primary_category") == "deposit_payment_problems"
    ]
    unique_deposit_groups = set()
    for item in deposit_items:
        gid = item.get("duplicate_group_id") or item.get("content_hash") or item.get("id")
        unique_deposit_groups.add(gid)

    if len(unique_deposit_groups) >= deposit_threshold:
        alerts.append({
            "alert_level": "INCREASED_CONCERN",
            "rule_name": "DEPOSIT_ISSUES_ELEVATED",
            "title": "Multiple Payment / Deposit Anomalies Reported",
            "description": f"{len(unique_deposit_groups)} unique reports indicate payment or deposit friction.",
            "evidence_summary": f"Identified across {len(deposit_items)} total mentions."
        })

    # -------------------------------------------------------------
    # 4. Check Regulatory & Enforcement Actions
    # -------------------------------------------------------------
    regulatory_items = [
        item for item in collected_items
        if item.get("primary_category") == "corporate_regulatory_developments"
    ]
    if regulatory_items:
        titles = [f"[{r.get('source_name', 'Source')}] {r.get('title', '')[:80]}" for r in regulatory_items[:3]]
        alerts.append({
            "alert_level": "SERIOUS_WARNING",
            "rule_name": "REGULATORY_DEVELOPMENTS_DETECTED",
            "title": "Regulatory or Corporate Development Recorded",
            "description": f"Found {len(regulatory_items)} public mention(s) regarding corporate, legal, or regulatory scrutiny.",
            "evidence_summary": f"Reports: {'; '.join(titles)}"
        })

    # -------------------------------------------------------------
    # 5. Check Official Documentation Changes
    # -------------------------------------------------------------
    recent_changes = [
        dc for dc in doc_changes
        if dc.get("diff_summary") and dc.get("diff_summary") != "No text change detected."
    ]
    if recent_changes:
        details = [f"Snapshot #{dc.get('id')} ({dc.get('url', '')}): {dc.get('diff_summary')[:100]}" for dc in recent_changes[:2]]
        alerts.append({
            "alert_level": "INCREASED_CONCERN",
            "rule_name": "OFFICIAL_POLICY_CHANGED",
            "title": "Official GitBook Documentation Modified",
            "description": "Changes detected in official platform terms, documentation, or fee structure.",
            "evidence_summary": f"Diff: {'; '.join(details)}"
        })

    # -------------------------------------------------------------
    # 6. Overall Monitoring State Synthesis
    # -------------------------------------------------------------
    has_serious = any(a["alert_level"] == "SERIOUS_WARNING" for a in alerts)
    has_concern = any(a["alert_level"] == "INCREASED_CONCERN" for a in alerts)

    if has_serious:
        overall_posture = "SERIOUS_WARNING"
    elif has_concern:
        overall_posture = "INCREASED_CONCERN"
    else:
        overall_posture = "NORMAL"

    return overall_posture, alerts
