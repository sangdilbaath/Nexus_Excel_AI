"""
database.py — SQLite persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "/tmp/nexus.db"

PLAN_LABELS = {
    "none":         "No Plan",
    "free_trial":   "7-Day Free Trial",
    "basic":        "Basic",
    "premium":      "Premium",
    "pro":          "Pro",
}

def init_db() -> None:
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

def _row_to_dict(row: tuple) -> dict:
    return {
        "id":                  row[0],
        "email":               row[1],
        "plan_type":           row[2],
        "has_payment_on_file": bool(row[3]),
        "trial_start_date":    row[4],
        "trial_end_date":      row[5],
    }

def get_user(email: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None

def upsert_user(email: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()
    return get_user(email)

def has_used_trial(email: str) -> bool:
    """Return True if this email has EVER activated a free trial."""
    user = get_user(email)
    if not user:
        return False
    return user.get("trial_start_date") is not None

def activate_plan(email: str, plan_type: str) -> dict:
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
    if user["plan_type"] != "free_trial":
        return False
    if not user["trial_end_date"]:
        return False
    end = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
    return datetime.now() > end

def days_remaining(user: dict) -> int:
    if user["plan_type"] != "free_trial" or not user["trial_end_date"]:
        return 0
    end  = datetime.strptime(user["trial_end_date"], "%Y-%m-%d %H:%M:%S")
    diff = end - datetime.now()
    return max(0, diff.days)

import sqlite3
from datetime import datetime, timedelta

# --- PLAN CONFIGURATION ---
PLAN_LABELS = {
    'none': 'No Plan',
    'free_trial': '7-Day Free Trial',
    'basic': 'Basic Plan',
    'premium': 'Premium Plan',
    'pro': 'Pro Plan'
}

# --- BILLING & PLAN FUNCTIONS ---
def activate_plan(email, plan_type):
    """Activates the user's plan and calculates trial dates if needed."""
    # Connect directly to the SQLite file
    conn = sqlite3.connect('nexus.db') 
    cursor = conn.cursor()
    
    has_payment = True
    trial_start = None
    trial_end = None
    
    if plan_type == 'free_trial':
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=7)
        
    cursor.execute('''
        UPDATE users 
        SET plan_type = ?, has_payment_on_file = ?, trial_start_date = ?, trial_end_date = ?
        WHERE email = ?
    ''', (plan_type, has_payment, trial_start, trial_end, email))
    
    conn.commit()
    conn.close()

def has_used_trial(email):
    """Checks if a user has already used their 7-day free trial."""
    conn = sqlite3.connect('nexus.db')
    cursor = conn.cursor()
    cursor.execute('SELECT trial_start_date FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()
    
    # If there is a date in the database, they have used the trial
    return result is not None and result[0] is not None
