"""Database repository for SQLite storage and queries."""

import sqlite3
import os
import shutil
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class Repository:
    def __init__(self, db_path: str = "data/baf_risk_monitor.db"):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self, schema_file: Optional[str] = None) -> None:
        """Initialize the database schema."""
        target_schema = schema_file or SCHEMA_PATH
        if not os.path.exists(target_schema):
            raise FileNotFoundError(f"Schema file not found at {target_schema}")

        with open(target_schema, "r", encoding="utf-8") as f:
            sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(sql)
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # ==========================================
    # Sources Management
    # ==========================================

    def upsert_source(self, source: Dict[str, Any]) -> None:
        """Insert or update a monitored source definition."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sources (id, name, source_type, url, access_method, requires_key, enabled, updated_at)
                VALUES (:id, :name, :source_type, :url, :access_method, :requires_key, :enabled, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    source_type = excluded.source_type,
                    url = excluded.url,
                    access_method = excluded.access_method,
                    requires_key = excluded.requires_key,
                    enabled = excluded.enabled,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                source
            )
            conn.commit()

    def get_sources(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM sources ORDER BY id ASC")
            return [dict(row) for row in cur.fetchall()]

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_source_status(
        self,
        source_id: str,
        status: str,
        error: Optional[str] = None,
        last_run_at: Optional[datetime] = None
    ) -> None:
        run_timestamp = (last_run_at or datetime.now(timezone.utc)).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE sources
                SET last_status = ?, last_error = ?, last_run_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (status, error, run_timestamp, source_id)
            )
            conn.commit()

    # ==========================================
    # Collection Runs
    # ==========================================

    def create_collection_run(self, source_id: str, started_at: Optional[datetime] = None) -> int:
        start_time = (started_at or datetime.now(timezone.utc)).isoformat()
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO collection_runs (source_id, started_at, status)
                VALUES (?, ?, 'RUNNING');
                """,
                (source_id, start_time)
            )
            conn.commit()
            return cur.lastrowid

    def finish_collection_run(
        self,
        run_id: int,
        status: str,
        items_found: int = 0,
        items_saved: int = 0,
        error_message: Optional[str] = None,
        finished_at: Optional[datetime] = None
    ) -> None:
        finish_time = (finished_at or datetime.now(timezone.utc)).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE collection_runs
                SET status = ?, items_found = ?, items_saved = ?, error_message = ?, finished_at = ?
                WHERE id = ?;
                """,
                (status, items_found, items_saved, error_message, finish_time, run_id)
            )
            conn.commit()

    def get_collection_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT r.*, s.name as source_name
                FROM collection_runs r
                LEFT JOIN sources s ON r.source_id = s.id
                ORDER BY r.id DESC LIMIT ?;
                """,
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]

    # ==========================================
    # Collected Items (Idempotent Storage)
    # ==========================================

    def save_collected_item(self, item: Dict[str, Any]) -> bool:
        """
        Idempotently insert a collected item.
        Returns True if a new item was inserted, False if item already existed.
        """
        sec_cat = item.get("secondary_categories")
        if isinstance(sec_cat, list):
            sec_cat = json.dumps(sec_cat)

        metadata = item.get("raw_metadata")
        if isinstance(metadata, (dict, list)):
            metadata = json.dumps(metadata)

        query = """
            INSERT INTO collected_items (
                id, source_id, url, title, content_excerpt, content_hash,
                simhash, duplicate_group_id, published_at, collected_at,
                author, sentiment_label, sentiment_score, primary_category,
                secondary_categories, evidence_status, is_complaint, raw_metadata
            ) VALUES (
                :id, :source_id, :url, :title, :content_excerpt, :content_hash,
                :simhash, :duplicate_group_id, :published_at, :collected_at,
                :author, :sentiment_label, :sentiment_score, :primary_category,
                :secondary_categories, :evidence_status, :is_complaint, :raw_metadata
            )
            ON CONFLICT(id) DO NOTHING;
        """

        params = {
            "id": item["id"],
            "source_id": item["source_id"],
            "url": item["url"],
            "title": item["title"],
            "content_excerpt": item.get("content_excerpt", ""),
            "content_hash": item["content_hash"],
            "simhash": item.get("simhash"),
            "duplicate_group_id": item.get("duplicate_group_id"),
            "published_at": item.get("published_at"),
            "collected_at": item["collected_at"],
            "author": item.get("author"),
            "sentiment_label": item["sentiment_label"],
            "sentiment_score": item["sentiment_score"],
            "primary_category": item["primary_category"],
            "secondary_categories": sec_cat,
            "evidence_status": item["evidence_status"],
            "is_complaint": 1 if item.get("is_complaint") else 0,
            "raw_metadata": metadata,
        }

        with self.get_connection() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.rowcount > 0

    def get_collected_items(
        self,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        evidence_status: Optional[str] = None,
        source_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_complaint: Optional[bool] = None,
        search_query: Optional[str] = None,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []

        if category:
            clauses.append("i.primary_category = ?")
            params.append(category)
        if sentiment:
            clauses.append("i.sentiment_label = ?")
            params.append(sentiment)
        if evidence_status:
            clauses.append("i.evidence_status = ?")
            params.append(evidence_status)
        if source_id:
            clauses.append("i.source_id = ?")
            params.append(source_id)
        if start_date:
            clauses.append("date(coalesce(i.published_at, i.collected_at)) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(coalesce(i.published_at, i.collected_at)) <= date(?)")
            params.append(end_date)
        if is_complaint is not None:
            clauses.append("i.is_complaint = ?")
            params.append(1 if is_complaint else 0)
        if search_query:
            clauses.append("(i.title LIKE ? OR i.content_excerpt LIKE ?)")
            term = f"%{search_query}%"
            params.extend([term, term])

        where_stmt = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        sql = f"""
            SELECT i.*, s.name as source_name
            FROM collected_items i
            LEFT JOIN sources s ON i.source_id = s.id
            {where_stmt}
            ORDER BY coalesce(i.published_at, i.collected_at) DESC, i.collected_at DESC
            LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def count_collected_items(self) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM collected_items")
            return cur.fetchone()[0]

    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT i.*, s.name as source_name
                FROM collected_items i
                LEFT JOIN sources s ON i.source_id = s.id
                WHERE i.id = ?;
                """,
                (item_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # ==========================================
    # Official Documentation Snapshots & Diffs
    # ==========================================

    def get_latest_doc_snapshot(self, url: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT * FROM doc_snapshots
                WHERE url = ?
                ORDER BY snapshot_timestamp DESC LIMIT 1;
                """,
                (url,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def save_doc_snapshot(
        self,
        source_id: str,
        url: str,
        title: str,
        content_hash: str,
        raw_text: str,
        diff_summary: Optional[str] = None,
        previous_snapshot_id: Optional[int] = None
    ) -> int:
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO doc_snapshots (
                    source_id, url, title, snapshot_timestamp, content_hash,
                    raw_text, diff_summary, previous_snapshot_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (source_id, url, title, now_str, content_hash, raw_text, diff_summary, previous_snapshot_id)
            )
            conn.commit()
            return cur.lastrowid

    def get_doc_snapshots(self, url: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if url:
                cur = conn.execute(
                    "SELECT * FROM doc_snapshots WHERE url = ? ORDER BY snapshot_timestamp DESC LIMIT ?",
                    (url, limit)
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM doc_snapshots ORDER BY snapshot_timestamp DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cur.fetchall()]

    # ==========================================
    # Risk Alerts
    # ==========================================

    def save_risk_alert(
        self,
        alert_level: str,
        rule_name: str,
        title: str,
        description: str,
        evidence_summary: str
    ) -> int:
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO risk_alerts (
                    created_at, alert_level, rule_name, title, description, evidence_summary, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1);
                """,
                (now_str, alert_level, rule_name, title, description, evidence_summary)
            )
            conn.commit()
            return cur.lastrowid

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT * FROM risk_alerts
                WHERE is_active = 1
                ORDER BY created_at DESC;
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def get_all_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT * FROM risk_alerts
                ORDER BY created_at DESC LIMIT ?;
                """,
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]

    def acknowledge_alert(self, alert_id: int) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE risk_alerts SET is_active = 0, acknowledged_at = ? WHERE id = ?;",
                (now_str, alert_id)
            )
            conn.commit()

    # ==========================================
    # Daily Metrics Aggregation
    # ==========================================

    def save_or_update_daily_metrics(self, date_str: str, metrics: Dict[str, Any]) -> None:
        params = {
            "date": date_str,
            "total_items_collected": metrics.get("total_items_collected", 0),
            "positive_mentions": metrics.get("positive_mentions", 0),
            "negative_mentions": metrics.get("negative_mentions", 0),
            "neutral_mentions": metrics.get("neutral_mentions", 0),
            "mixed_mentions": metrics.get("mixed_mentions", 0),
            "complaint_volume": metrics.get("complaint_volume", 0),
            "corroborated_events": metrics.get("corroborated_events", 0),
            "doc_changes_detected": metrics.get("doc_changes_detected", 0),
            "active_sources_count": metrics.get("active_sources_count", 0),
            "failed_sources_count": metrics.get("failed_sources_count", 0),
            "monitoring_state": metrics.get("monitoring_state", "NORMAL"),
        }
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_metrics (
                    date, total_items_collected, positive_mentions, negative_mentions,
                    neutral_mentions, mixed_mentions, complaint_volume,
                    corroborated_events, doc_changes_detected, active_sources_count,
                    failed_sources_count, monitoring_state, updated_at
                ) VALUES (
                    :date, :total_items_collected, :positive_mentions, :negative_mentions,
                    :neutral_mentions, :mixed_mentions, :complaint_volume,
                    :corroborated_events, :doc_changes_detected, :active_sources_count,
                    :failed_sources_count, :monitoring_state, CURRENT_TIMESTAMP
                )
                ON CONFLICT(date) DO UPDATE SET
                    total_items_collected = excluded.total_items_collected,
                    positive_mentions = excluded.positive_mentions,
                    negative_mentions = excluded.negative_mentions,
                    neutral_mentions = excluded.neutral_mentions,
                    mixed_mentions = excluded.mixed_mentions,
                    complaint_volume = excluded.complaint_volume,
                    corroborated_events = excluded.corroborated_events,
                    doc_changes_detected = excluded.doc_changes_detected,
                    active_sources_count = excluded.active_sources_count,
                    failed_sources_count = excluded.failed_sources_count,
                    monitoring_state = excluded.monitoring_state,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                params
            )
            conn.commit()

    def get_daily_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []
        if start_date:
            clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("date <= ?")
            params.append(end_date)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with self.get_connection() as conn:
            cur = conn.execute(
                f"SELECT * FROM daily_metrics {where} ORDER BY date ASC;",
                params
            )
            return [dict(row) for row in cur.fetchall()]

    # ==========================================
    # Backup & Restore
    # ==========================================

    def backup_database(self, destination_dir: str = "data/backups") -> str:
        os.makedirs(destination_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"baf_risk_monitor_backup_{timestamp}.db"
        dest_path = os.path.join(destination_dir, backup_filename)

        # Use SQLite backup API for transactionally consistent snapshots
        with self.get_connection() as src_conn:
            dst_conn = sqlite3.connect(dest_path)
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()

        logger.info(f"Database successfully backed up to {dest_path}")
        return dest_path

    def restore_database(self, backup_file: str) -> None:
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found at {backup_file}")

        # Check validity by opening
        test_conn = sqlite3.connect(backup_file)
        try:
            test_conn.execute("SELECT count(*) FROM sqlite_master;")
        finally:
            test_conn.close()

        # Copy over current database
        shutil.copy2(backup_file, self.db_path)
        logger.info(f"Database successfully restored from {backup_file}")
