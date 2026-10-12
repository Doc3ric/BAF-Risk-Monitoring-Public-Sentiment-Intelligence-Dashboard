"""Database restoration utility for BAF Risk Monitor.
Safely validates and restores SQLite database from a previous backup file.
"""

import os
import sys
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.repository import Repository


def restore(backup_path: str):
    if not os.path.exists(backup_path):
        # Check if it was provided relative to ROOT_DIR
        alt_path = os.path.join(ROOT_DIR, backup_path)
        if os.path.exists(alt_path):
            backup_path = alt_path
        else:
            print(f"ERROR: Backup file not found at: {backup_path}")
            sys.exit(1)

    db_path = os.path.join(ROOT_DIR, "data", "baf_risk_monitor.db")
    repo = Repository(db_path=db_path)
    repo.restore_database(backup_path)
    print(f"SUCCESS: Database restored successfully from: {backup_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore BAF Risk Monitor database from backup file.")
    parser.add_argument("backup_file", help="Path to .db backup file")
    args = parser.parse_args()
    restore(args.backup_file)
