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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
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
    except Exception:
        pass


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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()
        return _row_to_dict(row) if row else None
    except Exception:
        return None


def upsert_user(email: str) -> dict:
    """Insert user if new; return user dict regardless."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email,))
        conn.commit()
        conn.close()
        return get_user(email) or {
            "email": email, "plan_type": "none", "has_payment_on_file": 0,
            "trial_start_date": None, "trial_end_date": None
        }
    except Exception:
        # Failsafe if DB locks up
        return {
            "email": email, "plan_type": "none", "has_payment_on_file": 0,
            "trial_start_date": None, "trial_end_date": None
        }


def activate_plan(email: str, plan_type: str) -> Optional[dict]:
    """
    Set plan + mark payment received.
    For free_trial, automatically set trial_start_date and trial_end_date.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()

        if plan_type == "free_trial":
            now         = datetime.now()
            trial_start = now.strftime("%Y-%m-%d %H:%M:%S")
            trial_end   = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                UPDATE users
                SET plan_type           = ?,
                    has_payment_on_file = 1,
                    trial_start_date    = ?,
                    trial_end_date      = ?
                WHERE email = ?
            """, (plan_type, trial_start, trial_end, email))
        else:
            # CRITICAL FIX: Do not overwrite trial_start and trial_end with None for Paid Plans
            c.execute("""
                UPDATE users
                SET plan_type           = ?,
                    has_payment_on_file = 1
                WHERE email = ?
            """, (plan_type, email))
            
        conn.commit()
        conn.close()
        return get_user(email)
    except Exception:
        return None


def has_used_trial(email: str) -> bool:
    """
    Return True if this email has EVER activated a free trial —
    even if it expired. Used to block repeat trial signups.
    """
    user = get_user(email)
    if not user:
        return False
    return user.get("trial_start_date") is not None


def is_trial_expired(user: dict) -> bool:
    """Return True if the user is on free_trial and the trial has ended."""
    if user.get("plan_type", "none") != "free_trial":
        return False
    if not user.get("trial_end_date"):
        return False
    try:
        end = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
        return datetime.now() > end
    except Exception:
        return False


def days_remaining(user: dict) -> int:
    """Return whole days left in trial (0 if expired or non-trial)."""
    if user.get("plan_type", "none") != "free_trial" or not user.get("trial_end_date"):
        return 0
    try:
        end  = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
        diff = end - datetime.now()
        return max(0, diff.days)
    except Exception:
        return 0
        # ── Admin Analytics & Control ──────────────────────────────────

def get_admin_stats() -> dict:
    """Returns aggregated data for the admin dashboard."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        # Total users
        c.execute("SELECT COUNT(*) FROM users")
        total = c.fetchone()[0]
        
        # Breakdown by plan
        c.execute("SELECT plan_type, COUNT(*) FROM users GROUP BY plan_type")
        plans = dict(c.fetchall())
        
        conn.close()
        return {"total_users": total, "plans": plans}
    except:
        return {"total_users": 0, "plans": {}}

def block_user_trial(email: str) -> bool:
    """Manually forces a user's trial to expire to block their access."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        # Set end date to yesterday to effectively expire it
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET trial_end_date = ? WHERE email = ?", (yesterday, email))
        conn.commit()
        conn.close()
        return True
    except:
        return False
