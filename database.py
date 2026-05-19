"""
database.py — SQLite persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "nexus.db")

PLAN_LABELS = {
    "none":         "No Plan",
    "free_trial":   "7-Day Free Trial",
    "basic":        "Basic",
    "premium":      "Premium",
    "pro":          "Pro",
}

# ── Schema ────────────────────────────────────────────────────
def init_db() -> None:
    """Create the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            email               TEXT    UNIQUE NOT NULL,
            plan_type           TEXT    DEFAULT 'none',
            has_payment_on_file INTEGER DEFAULT 0,
            trial_start_date    TEXT,
            trial_end_date      TEXT
        )
    """)
    conn.commit()
    conn.close()


# ── Helpers ───────────────────────────────────────────────────
def _row_to_dict(row: tuple) -> dict:
    return {
        "id":                  row[0],
        "email":               row[1],
        "plan_type":           row[2],
        "has_payment_on_file": bool(row[3]),
        "trial_start_date":    row[4],
        "trial_end_date":      row[5],
    }


# ── CRUD ──────────────────────────────────────────────────────
def get_user(email: str) -> Optional[dict]:
    """Return user dict or None if not found."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def upsert_user(email: str) -> dict:
    """Insert user if new; return user dict regardless."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()
    return get_user(email)


def activate_plan(email: str, plan_type: str) -> dict:
    """
    Set plan + mark payment received.
    For free_trial, automatically set trial_start_date and trial_end_date.
    """
    trial_start = None
    trial_end   = None

    if plan_type == "free_trial":
        now         = datetime.now()
        trial_start = now.strftime("%Y-%m-%d %H:%M:%S")
        trial_end   = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET plan_type           = ?,
            has_payment_on_file = 1,
            trial_start_date    = ?,
            trial_end_date      = ?
        WHERE email = ?
    """, (plan_type, trial_start, trial_end, email))
    conn.commit()
    conn.close()
    return get_user(email)


def is_trial_expired(user: dict) -> bool:
    """Return True if the user is on free_trial and the trial has ended."""
    if user["plan_type"] != "free_trial":
        return False
    if not user["trial_end_date"]:
        return False
    end = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
    return datetime.now() > end


def days_remaining(user: dict) -> int:
    """Return whole days left in trial (0 if expired or non-trial)."""
    if user["plan_type"] != "free_trial" or not user["trial_end_date"]:
        return 0
    end  = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
    diff = end - datetime.now()
    return max(0, diff.days)
