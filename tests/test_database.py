"""Tests for SQLite database schema, repository operations, idempotency, and backup/restore."""

import os
import tempfile
import pytest
from database.repository import Repository


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = Repository(db_path=db_path)
        repo.init_db()
        yield repo


def test_init_db(temp_repo):
    assert os.path.exists(temp_repo.db_path)
    sources = temp_repo.get_sources()
    assert isinstance(sources, list)


def test_source_lifecycle(temp_repo):
    source_data = {
        "id": "test_src",
        "name": "Test Source",
        "source_type": "rss",
        "url": "https://example.com/rss",
        "access_method": "RSS",
        "requires_key": 0,
        "enabled": 1
    }
    temp_repo.upsert_source(source_data)
    src = temp_repo.get_source("test_src")
    assert src is not None
    assert src["name"] == "Test Source"

    temp_repo.update_source_status("test_src", "FAILED", error="Timeout after 15s")
    src_updated = temp_repo.get_source("test_src")
    assert src_updated["last_status"] == "FAILED"
    assert src_updated["last_error"] == "Timeout after 15s"


def test_item_idempotency(temp_repo):
    temp_repo.upsert_source({
        "id": "src_1",
        "name": "Source 1",
        "source_type": "web",
        "url": "https://example.com",
        "access_method": "GET",
        "requires_key": 0,
        "enabled": 1
    })

    item = {
        "id": "item_12345",
        "source_id": "src_1",
        "url": "https://example.com/story1",
        "title": "BlockAlgo Test Story",
        "content_excerpt": "Test excerpt about BlockAlgo",
        "content_hash": "hash12345",
        "simhash": "0123456789abcdef",
        "duplicate_group_id": "group_1",
        "published_at": "2026-10-12T00:00:00",
        "collected_at": "2026-10-12T01:00:00",
        "author": "Analyst",
        "sentiment_label": "POSITIVE",
        "sentiment_score": 0.5,
        "primary_category": "independent_reporting",
        "secondary_categories": ["earnings_and_return_claims"],
        "evidence_status": "UNVERIFIED",
        "is_complaint": 0,
        "raw_metadata": {"note": "sample"}
    }

    # First insert succeeds
    saved1 = temp_repo.save_collected_item(item)
    assert saved1 is True
    assert temp_repo.count_collected_items() == 1

    # Second insert with same ID does not duplicate (idempotent)
    saved2 = temp_repo.save_collected_item(item)
    assert saved2 is False
    assert temp_repo.count_collected_items() == 1


def test_doc_snapshots_and_diffs(temp_repo):
    temp_repo.upsert_source({
        "id": "official_baf",
        "name": "Official BAF",
        "source_type": "official",
        "url": "https://baf-1.gitbook.io/baf/",
        "access_method": "GET",
        "requires_key": 0,
        "enabled": 1
    })

    snap_id = temp_repo.save_doc_snapshot(
        source_id="official_baf",
        url="https://baf-1.gitbook.io/baf/",
        title="Terms v1",
        content_hash="hash_v1",
        raw_text="BAF withdrawal fee: 2%",
        diff_summary="Baseline"
    )
    assert snap_id > 0

    latest = temp_repo.get_latest_doc_snapshot("https://baf-1.gitbook.io/baf/")
    assert latest["content_hash"] == "hash_v1"

    # Save second snapshot with diff
    snap_id2 = temp_repo.save_doc_snapshot(
        source_id="official_baf",
        url="https://baf-1.gitbook.io/baf/",
        title="Terms v2",
        content_hash="hash_v2",
        raw_text="BAF withdrawal fee: 10%",
        diff_summary="- fee: 2%\n+ fee: 10%",
        previous_snapshot_id=snap_id
    )
    latest2 = temp_repo.get_latest_doc_snapshot("https://baf-1.gitbook.io/baf/")
    assert latest2["content_hash"] == "hash_v2"
    assert latest2["previous_snapshot_id"] == snap_id


def test_backup_and_restore(temp_repo):
    temp_repo.upsert_source({
        "id": "src_backup_test",
        "name": "Backup Source",
        "source_type": "manual",
        "url": "https://example.com",
        "access_method": "manual",
        "requires_key": 0,
        "enabled": 1
    })

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as backup_dir:
        backup_file = temp_repo.backup_database(destination_dir=backup_dir)
        assert os.path.exists(backup_file)

        # Modify database
        temp_repo.upsert_source({
            "id": "modified_src",
            "name": "New Source",
            "source_type": "manual",
            "url": "https://new.com",
            "access_method": "manual",
            "requires_key": 0,
            "enabled": 1
        })
        assert temp_repo.get_source("modified_src") is not None

        # Restore from backup
        temp_repo.restore_database(backup_file)
        assert temp_repo.get_source("src_backup_test") is not None
        assert temp_repo.get_source("modified_src") is None
