"""
User database operations for TrendMuse (raw sqlite3).
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path(__file__).parent.parent.parent / "data" / "trendmuse.db"

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    full_name TEXT,
    google_id TEXT UNIQUE,
    credits_remaining INTEGER DEFAULT 50,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users table if it doesn't exist."""
    with _get_conn() as conn:
        conn.execute(CREATE_USERS_TABLE)
        conn.commit()


def _row_to_dict(row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return _row_to_dict(row)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row)


def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
        return _row_to_dict(row)


def deduct_credits(user_id: int, amount: int) -> int:
    """Deduct credits from user. Returns remaining credits. Raises ValueError if insufficient."""
    with _get_conn() as conn:
        row = conn.execute("SELECT credits_remaining FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise ValueError("User not found")
        current = row["credits_remaining"]
        if current < amount:
            raise ValueError(f"Insufficient credits: have {current}, need {amount}")
        new_balance = current - amount
        conn.execute("UPDATE users SET credits_remaining = ? WHERE id = ?", (new_balance, user_id))
        conn.commit()
        return new_balance


def create_user(
    email: str,
    username: str,
    hashed_password: Optional[str] = None,
    full_name: Optional[str] = None,
    google_id: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO users (email, username, hashed_password, full_name, google_id, credits_remaining, is_active, is_admin, created_at, subscription_tier, subscription_status)
               VALUES (?, ?, ?, ?, ?, 50, 1, 0, ?, 'free', 'inactive')""",
            (email, username, hashed_password, full_name, google_id, now),
        )
        conn.commit()
        return get_user_by_id(cursor.lastrowid)


def update_user_subscription(
    user_id: int,
    stripe_customer_id: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    subscription_status: Optional[str] = None,
    subscription_end_date: Optional[str] = None,
) -> bool:
    """Update user subscription information."""
    updates = []
    values = []
    
    if stripe_customer_id is not None:
        updates.append("stripe_customer_id = ?")
        values.append(stripe_customer_id)
    if subscription_tier is not None:
        updates.append("subscription_tier = ?")
        values.append(subscription_tier)
    if subscription_status is not None:
        updates.append("subscription_status = ?")
        values.append(subscription_status)
    if subscription_end_date is not None:
        updates.append("subscription_end_date = ?")
        values.append(subscription_end_date)
    
    if not updates:
        return False
        
    values.append(user_id)
    now = datetime.now(timezone.utc).isoformat()
    updates.append("updated_at = ?")
    values.append(now)
    
    with _get_conn() as conn:
        conn.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
        return True


def get_user_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's subscription information."""
    with _get_conn() as conn:
        row = conn.execute(
            """SELECT stripe_customer_id, subscription_tier, subscription_status, 
                      subscription_end_date, credits_remaining 
               FROM users WHERE id = ?""", 
            (user_id,)
        ).fetchone()
        return _row_to_dict(row)
