"""
database.py — Supabase (PostgreSQL) persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates, expiry_date, and passwords.
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional

PLAN_LABELS = {
    "none":         "No Plan",
    "trial":        "2-Day Trial",
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
    supabase = None
    print(f"Supabase Connection Error: {e}")

# ── Helpers ───────────────────────────────────────────────────
def _format_user(user: dict) -> dict:
    """Ensures the Supabase dictionary perfectly matches the old SQLite format."""
    if user:
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
            return False 
    else:
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

def admin_create_user(email: str, password: str, plan_type: str, duration_days: int) -> bool:
    """Admin function: Inserts or updates a user with a specific expiration."""
    if not supabase: return False
    try:
        # Strict Trial Rule
        if plan_type.lower() == "trial":
            duration_days = 2
            
        expiry_date = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        user = get_user(email)
        payload = {
            "password": password,
            "plan_type": plan_type,
            "has_payment_on_file": 1,
            "expiry_date": expiry_date,
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
    if user: return user
        
    default_user = {
        "email": email, "plan_type": "none", "has_payment_on_file": False,
        "trial_start_date": None, "trial_end_date": None, "expiry_date": None, "password": None
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
    Automatically assigns expiry_date for universal compliance.
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
                "trial_end_date": trial_end,
                "expiry_date": trial_end
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
    if not user: return False
    return user.get("trial_start_date") is not None

def is_account_expired(user: dict) -> bool:
    """Universal Check: Returns True if the current date is past the user's expiry_date."""
    if not user or not user.get("expiry_date"):
        return False # Indefinite access if no expiry is set
    try:
        # Slicing [:19] protects against minor timezone/Supabase formatting differences
        end = datetime.strptime(str(user["expiry_date"])[:19], "%Y-%m-%d %H:%M:%S")
        return datetime.now() > end
    except Exception:
        return False

def is_trial_expired(user: dict) -> bool:
    """Legacy check fallback."""
    return is_account_expired(user)

def days_remaining(user: dict) -> int:
    """Return whole days left in access (0 if expired)."""
    if not user.get("expiry_date"):
        return 0
    try:
        end  = datetime.strptime(str(user["expiry_date"])[:19], "%Y-%m-%d %H:%M:%S")
        diff = end - datetime.now()
        return max(0, diff.days)
    except Exception:
        return 0

# ── Admin Analytics & Control ──────────────────────────────────
def get_admin_stats() -> dict:
    """Returns aggregated data for the admin dashboard from Supabase."""
    if not supabase: return {"total_users": 0, "plans": {}}
    try:
        count_res = supabase.table("users").select("id", count="exact").execute()
        total = count_res.count if count_res.count is not None else 0
        
        plan_res = supabase.table("users").select("plan_type").execute()
        plans = {}
        for row in plan_res.data:
            pt = row.get("plan_type", "none")
            plans[pt] = plans.get(pt, 0) + 1
            
        return {"total_users": total, "plans": plans}
    except Exception:
        return {"total_users": 0, "plans": {}}

def block_user_trial(email: str) -> bool:
    """Manually forces a user's account/trial to expire."""
    if not supabase: return False
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("users").update({
            "expiry_date": yesterday, 
            "trial_end_date": yesterday
        }).eq("email", email).execute()
        return True
    except Exception:
        return False
