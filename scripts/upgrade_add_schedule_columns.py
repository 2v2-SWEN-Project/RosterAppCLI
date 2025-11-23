"""
Run this script to add `staff_id` and `admin_id` columns to the `schedule` table
if they do not already exist, and migrate `admin_id` from `created_by` where
appropriate.

Usage (from repository root):
  python3 scripts/upgrade_add_schedule_columns.py

This script uses SQLAlchemy and the application's `db` configuration. It runs
raw ALTER TABLE statements — make a DB backup before running in production.
"""
import sys
from sqlalchemy import text

from App.database import db


def column_exists(conn, table_name, column_name):
    q = text(
        "SELECT column_name FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
    )
    r = conn.execute(q, {"t": table_name, "c": column_name}).fetchone()
    return r is not None


def main():
    engine = db.engine
    conn = engine.connect()
    try:
        # Add staff_id if missing
        if not column_exists(conn, "schedule", "staff_id"):
            print("Adding column schedule.staff_id ...")
            conn.execute(text("ALTER TABLE schedule ADD COLUMN staff_id INTEGER"))
        else:
            print("Column schedule.staff_id already exists")

        # Add admin_id if missing
        if not column_exists(conn, "schedule", "admin_id"):
            print("Adding column schedule.admin_id ...")
            conn.execute(text("ALTER TABLE schedule ADD COLUMN admin_id INTEGER"))
        else:
            print("Column schedule.admin_id already exists")

        # Migrate admin_id from created_by where admin_id is NULL
        print("Migrating admin_id from created_by where admin_id IS NULL ...")
        conn.execute(text("UPDATE schedule SET admin_id = created_by WHERE admin_id IS NULL"))

        print("Done. Note: If your DB requires FK constraints you may want to add them manually.")
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
