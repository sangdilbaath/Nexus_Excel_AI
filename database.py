"""
database.py — Supabase (PostgreSQL) persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates, and passwords.
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional

PLAN_LABELS = {
    "none":         "No Plan",
    "free_trial":   "7-Day Free Trial",
    "basic":        "Basic",
    "premium":      "Premium",
    "pro":          "Pro",
}

# ── Connection Setup ──────────────────────────────────────────
@st.cache_resource
def init_connection() -> Client:
    """Initializes the Supabase client once and caches it for performance."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    # Fail gracefully if secrets aren't set up yet
    supabase = None
    print(f"Supabase Connection Error: {e}")

# ── Schema ────────────────────────────────────────────────────
def init_db() -> None:
    """
    Schema management is now handled entirely via the Supabase SQL Editor.
    This function remains to prevent breaking existing imports in Home.py/3_App.py.
    """
    pass

# ── Helpers ───────────────────────────────────────────────────
def _format_user(user: dict) -> dict:
    """Ensures the Supabase dictionary perfectly matches the old SQLite format."""
    if user:
        # The app expects this to be a boolean, just like the old SQLite bool(row[3])
        user["has_payment_on_file"] = bool(user.get("has_payment_on_file", 0))
    return user

# ── Auth & CRUD ───────────────────────────────────────────────
def get_user(email: str) -> Optional[dict]:
    """Return user dict or None if not found."""
    if not supabase: return None
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return _format_user(response.data[0])
        return None
    except Exception:
        return None

def verify_or_create_user(email: str, password: str):
    """
    Checks if email exists. If so, validates password.
    If not, creates a new user with the provided password.
    Returns user dict on success, False on incorrect password.
    """
    if not supabase: return False
    user = get_user(email)
    
    if user:
        # Handle legacy users who might not have a password yet
        if user.get("password") is None:
            try:
                supabase.table("users").update({"password": password}).eq("email", email).execute()
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
            new_user = {
                "email": email,
                "password": password,
                "plan_type": "none",
                "has_payment_on_file": 0
            }
            res = supabase.table("users").insert(new_user).execute()
            return _format_user(res.data[0]) if res.data else False
        except Exception:
            return False

def admin_create_user(email: str, password: str, plan_type: str) -> bool:
    """Admin function: Inserts or updates a user with an active paid plan."""
    if not supabase: return False
    try:
        user = get_user(email)
        payload = {
            "password": password,
            "plan_type": plan_type,
            "has_payment_on_file": 1,
            "trial_end_date": None
        }
        
        if user:
            supabase.table("users").update(payload).eq("email", email).execute()
        else:
            payload["email"] = email
            supabase.table("users").insert(payload).execute()
            
        return True
    except Exception:
        return False

def upsert_user(email: str) -> dict:
    """Legacy function, kept for safety in case of background calls."""
    user = get_user(email)
    if user:
        return user
        
    default_user = {
        "email": email, "plan_type": "none", "has_payment_on_file": False,
        "trial_start_date": None, "trial_end_date": None, "password": None
    }
    
    if not supabase: return default_user
    try:
        res = supabase.table("users").insert({
            "email": email, "plan_type": "none", "has_payment_on_file": 0
        }).execute()
        return _format_user(res.data[0]) if res.data else default_user
    except Exception:
        return default_user

def activate_plan(email: str, plan_type: str) -> Optional[dict]:
    """
    Set plan + mark payment received.
    For free_trial, automatically set trial_start_date and trial_end_date.
    """
    if not supabase: return None
    try:
        if plan_type == "free_trial":
            now         = datetime.now()
            trial_start = now.strftime("%Y-%m-%d %H:%M:%S")
            trial_end   = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            supabase.table("users").update({
                "plan_type": plan_type,
                "has_payment_on_file": 1,
                "trial_start_date": trial_start,
                "trial_end_date": trial_end
            }).eq("email", email).execute()
        else:
            supabase.table("users").update({
                "plan_type": plan_type,
                "has_payment_on_file": 1
            }).eq("email", email).execute()
            
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
        # Slicing [:19] protects against minor timezone differences if present
        end = datetime.strptime(user["trial_end_date"][:19], "%Y-%m-%d %H:%M:%S")
        return datetime.now() > end
    except Exception:
        return False

def days_remaining(user: dict) -> int:
    """Return whole days left in trial (0 if expired or non-trial)."""
    if user.get("plan_type", "none") != "free_trial" or not user.get("trial_end_date"):
        return 0
    try:
        end  = datetime.strptime(user["trial_end_date"][:19], "%Y-%m-%d %H:%M:%S")
        diff = end - datetime.now()
        return max(0, diff.days)
    except Exception:
        return 0

# ── Admin Analytics & Control ──────────────────────────────────
def get_admin_stats() -> dict:
    """Returns aggregated data for the admin dashboard from Supabase."""
    if not supabase: return {"total_users": 0, "plans": {}}
    try:
        # Fetch total user count
        count_res = supabase.table("users").select("id", count="exact").execute()
        total = count_res.count if count_res.count is not None else 0
        
        # Group users by plan_type (Supabase-py requires client-side grouping)
        plan_res = supabase.table("users").select("plan_type").execute()
        plans = {}
        for row in plan_res.data:
            pt = row.get("plan_type", "none")
            plans[pt] = plans.get(pt, 0) + 1
            
        return {"total_users": total, "plans": plans}
    except Exception:
        return {"total_users": 0, "plans": {}}

def block_user_trial(email: str) -> bool:
    """Manually forces a user's trial to expire to block their access."""
    if not supabase: return False
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("users").update({"trial_end_date": yesterday}).eq("email", email).execute()
        return True
    except Exception:
        return False
