"""Standalone Daily Collection Pipeline Script.
Executed automatically via Windows Task Scheduler or manually from CLI.
Operates completely independently of the Streamlit dashboard interface.
"""

import os
import sys
import logging
from datetime import datetime, timezone
import yaml
import zoneinfo

# Ensure workspace root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.repository import Repository
from collectors.official_baf import OfficialBAFCollector
from collectors.gdelt import GDELTCollector
from collectors.rss import RSSNewsCollector
from collectors.reddit import RedditCollector
from collectors.manual_import import ManualImportCollector
from analysis.daily_metrics import compute_daily_metrics_for_date
from analysis.risk_rules import evaluate_risk_posture

LOCK_FILE = os.path.join(ROOT_DIR, "data", "collector.lock")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "collector.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("collect_daily")


def load_settings() -> dict:
    settings_path = os.path.join(ROOT_DIR, "config", "settings.yaml")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def acquire_lock() -> bool:
    """Ensure no overlapping collector processes run simultaneously."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            # Check if process is still running on Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process != 0:
                kernel32.CloseHandle(process)
                logger.warning(f"Another collector process (PID {pid}) is currently running. Exiting.")
                return False
            else:
                # Stale lock
                logger.info(f"Removing stale lock file from inactive PID {pid}.")
                os.remove(LOCK_FILE)
        except Exception:
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass

    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception as e:
        logger.warning(f"Failed to remove lock file: {e}")


def run_all_collectors() -> dict:
    if not acquire_lock():
        return {"status": "ABORTED_LOCK_ACTIVE"}

    logger.info("==================================================")
    logger.info("Starting BAF Risk Monitor Daily Collection Run")
    logger.info(f"Execution Timestamp: {datetime.now(timezone.utc).isoformat()} UTC")
    logger.info("==================================================")

    settings = load_settings()
    db_path = os.path.join(ROOT_DIR, settings.get("app", {}).get("database_path", "data/baf_risk_monitor.db"))
    repo = Repository(db_path=db_path)
    repo.init_db()

    ua = settings.get("network", {}).get("user_agent")
    timeout = settings.get("network", {}).get("timeout_seconds", 15)
    sources_cfg = settings.get("sources", {})

    collectors = [
        OfficialBAFCollector(
            source_id=sources_cfg.get("official_baf", {}).get("id", "official_baf_docs"),
            name=sources_cfg.get("official_baf", {}).get("name", "BAF Official GitBook"),
            urls=sources_cfg.get("official_baf", {}).get("urls"),
            timeout=timeout,
            user_agent=ua
        ),
        GDELTCollector(
            source_id=sources_cfg.get("gdelt_news", {}).get("id", "gdelt_news"),
            name=sources_cfg.get("gdelt_news", {}).get("name", "GDELT News"),
            queries=sources_cfg.get("gdelt_news", {}).get("queries"),
            timeout=timeout,
            user_agent=ua
        ),
        RSSNewsCollector(
            source_id=sources_cfg.get("google_news_rss", {}).get("id", "google_news_rss"),
            name=sources_cfg.get("google_news_rss", {}).get("name", "Google News RSS"),
            feeds=sources_cfg.get("google_news_rss", {}).get("feeds"),
            timeout=timeout,
            user_agent=ua
        ),
        RedditCollector(
            source_id=sources_cfg.get("reddit_discussions", {}).get("id", "reddit_discussions"),
            name=sources_cfg.get("reddit_discussions", {}).get("name", "Reddit Discussions"),
            queries=sources_cfg.get("reddit_discussions", {}).get("search_queries"),
            timeout=timeout,
            user_agent=ua
        ),
        ManualImportCollector(
            source_id=sources_cfg.get("manual_import", {}).get("id", "manual_import"),
            name=sources_cfg.get("manual_import", {}).get("name", "Manual Uploads")
        )
    ]

    results = {}
    for c in collectors:
        c.register(repo)
        logger.info(f"Running collector: {c.name}...")
        res = c.run(repo)
        results[c.source_id] = res
        logger.info(f"Collector {c.name} finished: {res}")

    # Compute daily metrics in Asia/Manila timezone
    manila_tz = zoneinfo.ZoneInfo("Asia/Manila")
    today_manila = datetime.now(manila_tz).strftime("%Y-%m-%d")
    thresholds = settings.get("alert_rules", {})
    metrics = compute_daily_metrics_for_date(repo, today_manila, thresholds)
    logger.info(f"Daily metrics updated for {today_manila}: {metrics}")

    # Check and persist risk alerts
    items = repo.get_collected_items(limit=1000)
    sources = repo.get_sources()
    snapshots = repo.get_doc_snapshots(limit=50)
    posture, alerts = evaluate_risk_posture(items, sources, snapshots, thresholds)

    # Save new alerts if not already present
    existing_alerts = repo.get_active_alerts()
    existing_rules = {a["rule_name"] for a in existing_alerts}
    for alert in alerts:
        if alert["rule_name"] not in existing_rules:
            repo.save_risk_alert(
                alert_level=alert["alert_level"],
                rule_name=alert["rule_name"],
                title=alert["title"],
                description=alert["description"],
                evidence_summary=alert["evidence_summary"]
            )
            logger.warning(f"NEW RISK ALERT: [{alert['alert_level']}] {alert['title']}")

    release_lock()
    logger.info("Daily collection pipeline completed successfully.")
    return {"status": "SUCCESS", "results": results, "metrics": metrics, "posture": posture}


if __name__ == "__main__":
    run_all_collectors()
