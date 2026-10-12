"""Tests for collector lifecycle, error resiliency, manual imports, and timezone normalization."""

import os
import tempfile
import pytest
from database.repository import Repository
from collectors.base import BaseCollector
from collectors.manual_import import ManualImportCollector
from analysis.daily_metrics import to_manila_date


class MockFailingCollector(BaseCollector):
    def fetch_items(self):
        raise ConnectionError("DNS resolution failed for test host")


class MockSuccessfulCollector(BaseCollector):
    def fetch_items(self):
        return [
            {
                "title": "BlockAlgo announces new updates",
                "url": "https://example.com/baf-update",
                "content_excerpt": "BlockAlgo platform expands node infrastructure",
                "published_at": "2026-10-12T04:00:00Z",
                "author": "TechNews"
            }
        ]


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = os.path.join(tmpdir, "test_col.db")
        repo = Repository(db_path=db_path)
        repo.init_db()
        yield repo


def test_failing_collector_resilience(temp_repo):
    col = MockFailingCollector(
        source_id="mock_fail",
        name="Mock Failing Collector",
        source_type="news",
        url="https://fail.example.com"
    )
    col.register(temp_repo)
    result = col.run(temp_repo)

    assert result["status"] == "FAILED"
    assert "DNS resolution failed" in result["error"]

    # Verify database state
    source = temp_repo.get_source("mock_fail")
    assert source["last_status"] == "FAILED"
    assert "DNS resolution failed" in source["last_error"]

    runs = temp_repo.get_collection_runs(limit=1)
    assert len(runs) == 1
    assert runs[0]["status"] == "FAILED"


def test_successful_collector_saves_items(temp_repo):
    col = MockSuccessfulCollector(
        source_id="mock_success",
        name="Mock Successful Collector",
        source_type="news",
        url="https://example.com"
    )
    col.register(temp_repo)
    result = col.run(temp_repo)

    assert result["status"] == "SUCCESS"
    assert result["items_saved"] == 1

    items = temp_repo.get_collected_items()
    assert len(items) == 1
    assert "BlockAlgo" in items[0]["title"]
    assert items[0]["sentiment_label"] in ("POSITIVE", "NEUTRAL")


def test_manual_import_collector(temp_repo):
    col = ManualImportCollector()
    col.register(temp_repo)

    res = col.import_single_item(
        repo=temp_repo,
        title="SEC Philippines Advisory on BAF",
        url="https://sec.gov.ph/advisories/baf-notice",
        content="The Commission issues advisory warning the public regarding unauthorized investment offerings.",
        source_label="SEC Philippines",
        forced_category="corporate_regulatory_developments",
        forced_evidence_status="CORROBORATED"
    )

    assert res["status"] == "SUCCESS"
    items = temp_repo.get_collected_items()
    assert len(items) == 1
    assert items[0]["primary_category"] == "corporate_regulatory_developments"
    assert items[0]["evidence_status"] == "CORROBORATED"


def test_manual_import_csv(temp_repo):
    col = ManualImportCollector()
    col.register(temp_repo)

    csv_data = (
        "title,url,content,source,category,evidence_status\n"
        "User complaint on withdrawal,https://reddit.com/r/crypto/1,BlockAlgo cannot withdraw funds,Reddit,withdrawal_issues,REPORTED_ALLEGATION\n"
        "Review of BAF platform,https://medium.com/review,BlockAlgo passive income returns review,Medium,earnings_and_return_claims,PERSONAL_TESTIMONIAL\n"
    )

    res = col.import_from_csv(temp_repo, csv_data)
    assert res["total_rows"] == 2
    assert res["saved_count"] == 2
    assert temp_repo.count_collected_items() == 2


def test_to_manila_date_conversion():
    utc_iso = "2026-10-12T00:00:00Z"
    manila_date = to_manila_date(utc_iso)
    assert manila_date == "2026-10-12"

    utc_iso_evening = "2026-10-11T20:00:00Z"
    assert to_manila_date(utc_iso_evening) == "2026-10-12"
