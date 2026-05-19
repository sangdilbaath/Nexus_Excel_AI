"""
pages/3_App.py — Nexus Excel AI · Main AI Dashboard
Access-controlled, feature-gated AI data analyst powered by Gemini 2.5.
"""

import streamlit as st
import sys, os, re, io, time, datetime, concurrent.futures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from database import init_db, is_trial_expired, days_remaining, PLAN_LABELS
from styles import GLOBAL_CSS, APP_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS,    unsafe_allow_html=True)

init_db()

# ============================================================
# ACCESS CONTROL
# ============================================================
user = st.session_state.get("user")

# No user at all → back to home
if not user:
    st.switch_page("Home.py")

# Refresh user from DB (in case page was reloaded)
from database import get_user
email = st.session_state.get("email", user.get("email", ""))
if email:
    fresh = get_user(email)
    if fresh:
        user = fresh
        st.session_state["user"] = fresh

# Not paid → billing
if not user.get("has_payment_on_file"):
    st.switch_page("pages/2_Billing.py")

plan       = user.get("plan_type", "none")
trial_exp  = is_trial_expired(user)
is_admin   = st.session_state.get("is_admin", False)

# ── Master Key Overrides ──────────────────────────────────────
if is_admin:
    trial_exp = False
    plan = "pro"

# ── Trial expiry wall ─────────────────────────────────────────
if trial_exp:
    st.markdown("""
    <div style="text-align:center; padding:5rem 1rem;">
        <div style="font-size:3rem;">⏰</div>
        <h2 style="font-family:'Space Mono',monospace; color:#e6edf3; margin:1rem 0 0.5rem 0;">
            Your Free Trial Has Expired
        </h2>
        <p style="color:#8b949e; font-size:1rem; max-width:460px; margin:0 auto 2rem auto;">
            Your 7-day trial ended. Upgrade to a paid plan to continue using Nexus Excel AI.
        </p>
    </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([2, 1, 2])
    with col_btn:
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        if st.button("🚀 Upgrade My Plan", use_container_width=True):
            st.session_state.pop("plan_selected", None)
            st.switch_page("pages/1_Pricing.py")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Feature flags from plan ────────────────────────────────────
VOICE_ENABLED  = plan in ("free_trial", "premium", "pro") or is_admin
CHART_ENABLED  = plan in ("free_trial", "pro") or is_admin

# ============================================================
# CONSTANTS
# ============================================================
MAX_FILE_SIZE_MB         = 10
# Unlimited requests for admin
MAX_REQUESTS_PER_SESSION = 99999 if is_admin else 50
AI_TIMEOUT_SECONDS       = 30
PYTHON_KEYWORDS          = {'import', 'def', 'df', 'plt', 'pd', 'for', 'if', 'print', 'return', '=', 'fig', 'ax'}

# ============================================================
# SESSION STATE
# ============================================================
for key, default in {
    "query_text":      "",
    "updated_df":      None,
    "chart_gallery":   [],
    "command_history": [],
    "df":              None,
    "last_filename":   None,
    "show_all_data":   False,
    "show_all_cols":   False,
    "request_count":   0,
    "is_recording":    False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# HELPERS
# ============================================================
def clean_ai_code(raw: str) -> str:
    raw = re.sub(r"
http://googleusercontent.com/immersive_entry_chip/0
