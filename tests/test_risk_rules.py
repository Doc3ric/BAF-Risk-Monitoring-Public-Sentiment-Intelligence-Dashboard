"""Tests for risk posture rules, alert triggers, and explainable evidence generation."""

from analysis.risk_rules import evaluate_risk_posture


def test_normal_monitoring_posture():
    items = []
    sources = [{"name": "GDELT", "enabled": 1, "last_status": "SUCCESS", "last_run_at": "2026-10-12T10:00:00"}]
    doc_changes = []
    thresholds = {"withdrawal_complaints_threshold": 3, "deposit_problems_threshold": 3}

    posture, alerts = evaluate_risk_posture(items, sources, doc_changes, thresholds)
    assert posture == "NORMAL"
    assert len(alerts) == 0


def test_withdrawal_complaint_spike_alert():
    # 3 distinct withdrawal complaints
    items = [
        {
            "id": "1",
            "duplicate_group_id": "g1",
            "primary_category": "withdrawal_issues",
            "title": "User cannot withdraw USDT",
            "source_name": "Reddit"
        },
        {
            "id": "2",
            "duplicate_group_id": "g2",
            "primary_category": "withdrawal_issues",
            "title": "Pending withdrawal for 5 days",
            "source_name": "Forums"
        },
        {
            "id": "3",
            "duplicate_group_id": "g3",
            "primary_category": "withdrawal_issues",
            "title": "Cashout error 500",
            "source_name": "Telegram"
        }
    ]
    sources = [{"name": "Reddit", "enabled": 1, "last_status": "SUCCESS", "last_run_at": "2026-10-12T10:00:00"}]
    doc_changes = []
    thresholds = {"withdrawal_complaints_threshold": 3}

    posture, alerts = evaluate_risk_posture(items, sources, doc_changes, thresholds)
    assert posture == "SERIOUS_WARNING"
    assert any(a["rule_name"] == "WITHDRAWAL_COMPLAINTS_SPIKE" for a in alerts)
    # Ensure evidence summary lists underlying items
    withdrawal_alert = next(a for a in alerts if a["rule_name"] == "WITHDRAWAL_COMPLAINTS_SPIKE")
    assert "User cannot withdraw" in withdrawal_alert["evidence_summary"]


def test_duplicate_complaints_do_not_inflate_spike():
    # 3 items, but all share the SAME duplicate_group_id (e.g. syndicated repost of same tweet)
    items = [
        {
            "id": "1",
            "duplicate_group_id": "shared_group",
            "primary_category": "withdrawal_issues",
            "title": "Copied message: withdrawal failed",
            "source_name": "Site A"
        },
        {
            "id": "2",
            "duplicate_group_id": "shared_group",
            "primary_category": "withdrawal_issues",
            "title": "Copied message: withdrawal failed",
            "source_name": "Site B"
        },
        {
            "id": "3",
            "duplicate_group_id": "shared_group",
            "primary_category": "withdrawal_issues",
            "title": "Copied message: withdrawal failed",
            "source_name": "Site C"
        }
    ]
    sources = [{"name": "Site A", "enabled": 1, "last_status": "SUCCESS", "last_run_at": "2026-10-12T10:00:00"}]
    doc_changes = []
    thresholds = {"withdrawal_complaints_threshold": 3}

    posture, alerts = evaluate_risk_posture(items, sources, doc_changes, thresholds)
    # Should NOT trigger withdrawal spike because unique groups = 1 < threshold 3
    assert not any(a["rule_name"] == "WITHDRAWAL_COMPLAINTS_SPIKE" for a in alerts)


def test_regulatory_warning_alert():
    items = [
        {
            "id": "reg1",
            "primary_category": "corporate_regulatory_developments",
            "title": "SEC Advisory against unauthorized investment schemes mentioning BAF",
            "source_name": "SEC Philippines"
        }
    ]
    sources = [{"name": "SEC", "enabled": 1, "last_status": "SUCCESS"}]
    doc_changes = []
    thresholds = {}

    posture, alerts = evaluate_risk_posture(items, sources, doc_changes, thresholds)
    assert posture == "SERIOUS_WARNING"
    assert any(a["rule_name"] == "REGULATORY_DEVELOPMENTS_DETECTED" for a in alerts)


def test_failed_source_alert():
    items = []
    sources = [
        {"name": "GDELT API", "enabled": 1, "last_status": "FAILED", "last_error": "Connection reset by peer"}
    ]
    doc_changes = []
    thresholds = {}

    posture, alerts = evaluate_risk_posture(items, sources, doc_changes, thresholds)
    assert posture == "INCREASED_CONCERN"
    assert any(a["rule_name"] == "SOURCE_COLLECTION_FAILURE" for a in alerts)
    failure_alert = next(a for a in alerts if a["rule_name"] == "SOURCE_COLLECTION_FAILURE")
    assert "GDELT API" in failure_alert["evidence_summary"]
