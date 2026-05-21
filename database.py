"""
database.py — SQLite persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates, and passwords.
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
    """Create the users table if it doesn't exist, and update schema if needed."""
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
                trial_end_date      TEXT,
                password            TEXT
            )
        """)
        conn.commit()
        
        # Gracefully add password column to existing databases
        try:
            c.execute("ALTER TABLE users ADD COLUMN password TEXT")
            conn.commit()
        except Exception:
            pass # Column already exists
            
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
        "password":            row[6] if len(row) > 6 else None
    }


# ── Auth & CRUD ───────────────────────────────────────────────
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


def verify_or_create_user(email: str, password: str):
    """
    Checks if email exists. If so, validates password.
    If not, creates a new user with the provided password.
    Returns user dict on success, False on incorrect password.
    """
    user = get_user(email)
    
    if user:
        # Handle legacy users who signed up before passwords existed
        if user.get("password") is None:
            try:
                conn = sqlite3.connect(DB_PATH, timeout=10)
                c = conn.cursor()
                c.execute("UPDATE users SET password = ? WHERE email = ?", (password, email))
                conn.commit()
                conn.close()
                user["password"] = password
                return user
            except Exception:
                return False
                
        elif user.get("password") == password:
            return user
        else:
            return False # Incorrect password
    else:
        # Create new user
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password, plan_type, has_payment_on_file) VALUES (?, ?, 'none', 0)", (email, password))
            conn.commit()
            conn.close()
            return get_user(email)
        except Exception:
            return False


def admin_create_user(email: str, password: str, plan_type: str) -> bool:
    """Admin function: Inserts or updates a user with an active paid plan."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        user = get_user(email)
        
        if user:
            c.execute("""
                UPDATE users 
                SET password = ?, plan_type = ?, has_payment_on_file = 1, trial_end_date = NULL
                WHERE email = ?
            """, (password, plan_type, email))
        else:
            c.execute("""
                INSERT INTO users (email, password, plan_type, has_payment_on_file, trial_end_date)
                VALUES (?, ?, ?, 1, NULL)
            """, (email, password, plan_type))
            
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def upsert_user(email: str) -> dict:
    """Legacy function, kept for safety in case of background calls."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email,))
        conn.commit()
        conn.close()
        return get_user(email) or {
            "email": email, "plan_type": "none", "has_payment_on_file": 0,
            "trial_start_date": None, "trial_end_date": None, "password": None
        }
    except Exception:
        return {
            "email": email, "plan_type": "none", "has_payment_on_file": 0,
            "trial_start_date": None, "trial_end_date": None, "password": None
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
    """Return True if this email has EVER activated a free trial."""
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
        c.execute("SELECT COUNT(*) FROM users")
        total = c.fetchone()[0]
        
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
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET trial_end_date = ? WHERE email = ?", (yesterday, email))
        conn.commit()
        conn.close()
        return True
    except:
        return False
