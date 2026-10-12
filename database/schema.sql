-- BAF Risk Monitor - SQLite Database Schema

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    url TEXT,
    access_method TEXT,
    requires_key INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1,
    last_run_at TIMESTAMP,
    last_status TEXT DEFAULT 'PENDING',
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,
    items_found INTEGER DEFAULT 0,
    items_saved INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collected_items (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content_excerpt TEXT,
    content_hash TEXT NOT NULL,
    simhash TEXT,
    duplicate_group_id TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP NOT NULL,
    author TEXT,
    sentiment_label TEXT NOT NULL,
    sentiment_score REAL NOT NULL,
    primary_category TEXT NOT NULL,
    secondary_categories TEXT,
    evidence_status TEXT NOT NULL,
    is_complaint INTEGER DEFAULT 0,
    raw_metadata TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_collected_items_published ON collected_items(published_at);
CREATE INDEX IF NOT EXISTS idx_collected_items_collected ON collected_items(collected_at);
CREATE INDEX IF NOT EXISTS idx_collected_items_category ON collected_items(primary_category);
CREATE INDEX IF NOT EXISTS idx_collected_items_sentiment ON collected_items(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_collected_items_content_hash ON collected_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_collected_items_duplicate_group ON collected_items(duplicate_group_id);

CREATE TABLE IF NOT EXISTS doc_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    snapshot_timestamp TIMESTAMP NOT NULL,
    content_hash TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    diff_summary TEXT,
    previous_snapshot_id INTEGER,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE,
    FOREIGN KEY(previous_snapshot_id) REFERENCES doc_snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_doc_snapshots_url ON doc_snapshots(url);
CREATE INDEX IF NOT EXISTS idx_doc_snapshots_time ON doc_snapshots(snapshot_timestamp);

CREATE TABLE IF NOT EXISTS risk_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL,
    alert_level TEXT NOT NULL, -- 'NORMAL', 'INCREASED_CONCERN', 'SERIOUS_WARNING'
    rule_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_summary TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    acknowledged_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_alerts_level ON risk_alerts(alert_level);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_created ON risk_alerts(created_at);

CREATE TABLE IF NOT EXISTS daily_metrics (
    date TEXT PRIMARY KEY, -- YYYY-MM-DD
    total_items_collected INTEGER DEFAULT 0,
    positive_mentions INTEGER DEFAULT 0,
    negative_mentions INTEGER DEFAULT 0,
    neutral_mentions INTEGER DEFAULT 0,
    mixed_mentions INTEGER DEFAULT 0,
    complaint_volume INTEGER DEFAULT 0,
    corroborated_events INTEGER DEFAULT 0,
    doc_changes_detected INTEGER DEFAULT 0,
    active_sources_count INTEGER DEFAULT 0,
    failed_sources_count INTEGER DEFAULT 0,
    monitoring_state TEXT DEFAULT 'NORMAL',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
