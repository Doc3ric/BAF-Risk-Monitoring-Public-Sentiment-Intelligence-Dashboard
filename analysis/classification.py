"""Classification engine for BAF entity matching, issue categories, and evidence statuses.
Rule-based, fully explainable, configurable via config/keywords.yaml.
"""

import os
import re
import yaml
from typing import Dict, Any, List, Tuple

KEYWORDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "keywords.yaml")


def load_keywords_config() -> Dict[str, Any]:
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_config_cache: Dict[str, Any] = None


def get_config() -> Dict[str, Any]:
    global _config_cache
    if _config_cache is None:
        _config_cache = load_keywords_config()
    return _config_cache


def is_baf_relevant(title: str, content: str) -> Tuple[bool, str]:
    """
    Check if the text pertains to BlockAlgo Frontier / BAF.
    Returns (is_relevant, matched_entity).
    """
    cfg = get_config()
    combined = f"{title or ''} {content or ''}".lower()

    # Check primary entities (high confidence)
    for term in cfg.get("entities", {}).get("primary", ["blockalgo", "blockalgo frontier"]):
        if re.search(r"\b" + re.escape(term) + r"\b", combined):
            return True, term

    # Check secondary entities (require context)
    for term in cfg.get("entities", {}).get("secondary", ["baf platform", "baf technologies"]):
        if re.search(r"\b" + re.escape(term) + r"\b", combined):
            return True, term

    return False, ""


def classify_content(title: str, content: str) -> Dict[str, Any]:
    """
    Classify content into primary and secondary categories, scoring each category.
    Returns dict with primary_category, secondary_categories, scores, and is_complaint.
    """
    cfg = get_config()
    categories_cfg = cfg.get("categories", {})
    combined = f"{title or ''} {content or ''}".lower()

    scores: Dict[str, int] = {}

    for cat_id, cat_info in categories_cfg.items():
        score = 0
        keywords = cat_info.get("keywords", [])
        for kw in keywords:
            # Word boundary regex or phrase matching
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            matches = len(re.findall(pattern, combined))
            if matches > 0:
                score += matches * 2
            elif kw.lower() in combined:
                score += 1

        if score > 0:
            scores[cat_id] = score

    if not scores:
        primary = "independent_reporting"
        secondaries = []
    else:
        # Sort by score descending
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_cats[0][0]
        secondaries = [c[0] for c in sorted_cats[1:]]

    complaint_categories = {
        "withdrawal_issues",
        "deposit_payment_problems",
        "refund_complaints",
        "customer_support_complaints",
        "platform_downtime",
        "corporate_regulatory_developments"
    }

    # High-signal complaint and fraud warning keywords in text
    complaint_signals = [
        "complaint", "complaining", "warning", "warn", "scam", "scammer", "scammers",
        "ponzi", "pyramid", "fraud", "victim", "frozen", "freeze", "cannot withdraw",
        "unable to withdraw", "delay", "delays", "unresponsive", "ghosted", "fake",
        "loss", "lost money", "tax fee", "advisory"
    ]

    has_complaint_signal = any(sig in combined for sig in complaint_signals)
    is_complaint = (primary in complaint_categories or any(c in complaint_categories for c in secondaries) or has_complaint_signal)

    return {
        "primary_category": primary,
        "secondary_categories": secondaries,
        "category_scores": scores,
        "is_complaint": is_complaint
    }


def determine_evidence_status(
    source_type: str,
    primary_category: str,
    is_complaint: bool,
    sentiment_label: str,
    is_corroborated: bool = False
) -> str:
    """
    Assign an objective evidence status:
    - OFFICIAL_STATEMENT
    - CORROBORATED
    - REPORTED_ALLEGATION
    - PERSONAL_TESTIMONIAL
    - UNVERIFIED
    - UNABLE_TO_VERIFY
    """
    if source_type in ("official", "official_baf"):
        return "OFFICIAL_STATEMENT"

    if is_corroborated:
        return "CORROBORATED"

    if primary_category == "corporate_regulatory_developments":
        return "CORROBORATED" if is_corroborated else "REPORTED_ALLEGATION"

    if is_complaint:
        return "REPORTED_ALLEGATION"

    if primary_category in ("recruitment_and_referrals", "earnings_and_return_claims"):
        return "PERSONAL_TESTIMONIAL"

    if sentiment_label in ("POSITIVE", "NEGATIVE"):
        return "PERSONAL_TESTIMONIAL"

    return "UNVERIFIED"
