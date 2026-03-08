"""
Database migrations for TrendMuse auth system.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "trendmuse.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def add_subscription_fields():
    """Add subscription-related fields to users table."""
    with _get_conn() as conn:
        # Add stripe_customer_id column
        try:
            conn.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
                
        # Add subscription_tier column
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
                
        # Add subscription_status column
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'inactive'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
                
        # Add subscription_end_date column
        try:
            conn.execute("ALTER TABLE users ADD COLUMN subscription_end_date TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        conn.commit()
        print("✅ Subscription fields added to users table")


def run_migrations():
    """Run all database migrations."""
    add_subscription_fields()


if __name__ == "__main__":
    run_migrations()