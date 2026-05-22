"""
pages/5_Admin_Panel.py — Nexus Excel AI · Admin Dashboard
Dedicated dashboard for system analytics, user access control, and database management.
"""

import streamlit as st
import sys, os

# Ensure the app can find your root modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from styles import GLOBAL_CSS, APP_CSS
from database import get_admin_stats, block_user_trial, admin_create_user

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Admin Panel",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS, unsafe_allow_html=True)

# ============================================================
# ACCESS CONTROL
# ============================================================
if not st.session_state.get("is_admin"):
    st.switch_page("Home.py")

# ============================================================
# HERO SECTION
# ============================================================
st.markdown("""
<div class="hero-zone fade-up">
    <div class="hero-title">👑 Admin Control Panel</div>
    <div class="hero-sub">Manage users, view system analytics, and control platform access.</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SYSTEM ANALYTICS
# ============================================================
st.markdown('<div class="section-label">System Analytics</div>', unsafe_allow_html=True)

# Fetch stats from the database
stats = get_admin_stats()
total_users = stats.get('total_users', 0)
pro_users = stats.get('plans', {}).get('pro', 0)
trial_users = stats.get('plans', {}).get('free_trial', 0) + stats.get('plans', {}).get('trial', 0)

# Render identical metric cards to the main app
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="label">Total Users</div>
        <div class="value">{total_users:,}</div>
        <div class="sub">Registered accounts</div>
    </div>
    <div class="metric-card">
        <div class="label">Pro Plan Users</div>
        <div class="value">{pro_users:,}</div>
        <div class="sub">Paid subscriptions</div>
    </div>
    <div class="metric-card">
        <div class="label">Active Trials</div>
        <div class="value">{trial_users:,}</div>
        <div class="sub">Users on trial access</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# MANUAL USER REGISTRATION
# ============================================================
st.markdown('<div class="section-label">Register New User</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
        <strong style="color: var(--text-primary); font-family: var(--font-body); font-size: 1.1rem;">Manual User Registration</strong><br>
        <span style="color: var(--text-muted); font-size: 0.85rem;">Create a new user account with a specific expiration date. Bypasses the checkout flow entirely.</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_em, col_pw = st.columns(2)
    with col_em:
        new_email = st.text_input("User Email Address", placeholder="client@domain.com")
    with col_pw:
        new_password = st.text_input("Password", type="password")
        
    col_pl, col_dur = st.columns(2)
    with col_pl:
        new_plan = st.selectbox("Assign Plan", ["Trial", "Basic", "Premium", "Pro"])
    
    with col_dur:
        if new_plan == "Trial":
            st.info("ℹ️ Trials are strictly limited to 2 days.")
            duration_days = 2
        else:
            duration_days = st.number_input("Duration (Days)", min_value=1, value=30, step=1)
        
    st.markdown('<div class="cta-btn" style="max-width: 200px; margin-top: 0.5rem;">', unsafe_allow_html=True)
    register_btn = st.button("➕ Create Account", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if register_btn:
        if new_email and new_password:
            clean_email = new_email.strip().lower()
            plan_key = new_plan.lower()
            
            if admin_create_user(clean_email, new_password, plan_key, duration_days):
                st.success(f"✅ Account created for **{clean_email}** on **{new_plan}** (Expires in {duration_days} days).")
            else:
                st.error("❌ Failed to create user. Check database connection.")
        else:
            st.warning("⚠️ Both Email and Password are required.")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# ACCESS CONTROL (BLOCK USER)
# ============================================================
st.markdown('<div class="section-label">Access Control</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
        <strong style="color: var(--text-primary); font-family: var(--font-body); font-size: 1.1rem;">Block User / Expire Access</strong><br>
        <span style="color: var(--text-muted); font-size: 0.85rem;">Instantly expire a user's plan. They will be locked out of the dashboard immediately.</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_input, col_btn = st.columns([3, 1])
    
    with col_input:
        target_email = st.text_input(
            "User Email Address", 
            placeholder="e.g., user@domain.com", 
            label_visibility="collapsed",
            key="block_email"
        )
    
    with col_btn:
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        block_btn = st.button("🚫 Block Access", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if block_btn:
            clean_email = target_email.strip().lower()
            if clean_email:
                if block_user_trial(clean_email):
                    st.success(f"✅ Access successfully expired for {clean_email}.")
                else:
                    st.error("❌ Failed to block user. Check database connection.")
            else:
                st.warning("⚠️ Please enter a valid email address.")

# ============================================================
# DATABASE MANAGEMENT (CLOUD)
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Database Management</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
        <strong style="color: var(--text-primary); font-family: var(--font-body); font-size: 1.1rem;">Cloud Database (Supabase)</strong><br>
        <span style="color: var(--text-muted); font-size: 0.85rem;">Your database is now permanently hosted in the cloud. To view user tables, run SQL queries, or export backups, please log in to your Supabase dashboard.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="cta-btn" style="max-width: 250px;">', unsafe_allow_html=True)
    st.link_button("↗ Open Supabase Dashboard", "https://supabase.com/dashboard", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# NAVIGATION
# ============================================================
st.divider()

col_back, _ = st.columns([1, 4])
with col_back:
    if st.button("← Back to Portal", use_container_width=True):
        st.switch_page("pages/4_Admin_Portal.py")
