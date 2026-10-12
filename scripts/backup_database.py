"""Database backup utility for BAF Risk Monitor.
Creates a transactionally consistent copy of the SQLite database.
"""

import os
import sys
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.repository import Repository


def backup(dest_dir: str = "data/backups") -> str:
    db_path = os.path.join(ROOT_DIR, "data", "baf_risk_monitor.db")
    target_backup_dir = os.path.join(ROOT_DIR, dest_dir)
    repo = Repository(db_path=db_path)
    backup_file = repo.backup_database(destination_dir=target_backup_dir)
    print(f"SUCCESS: Database backup created at: {backup_file}")
    return backup_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup BAF Risk Monitor SQLite database.")
    parser.add_argument("--dest", default="data/backups", help="Destination folder for backup file")
    args = parser.parse_args()
    backup(dest_dir=args.dest)
