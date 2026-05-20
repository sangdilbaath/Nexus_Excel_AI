"""pages/5_Admin_Panel.py — Admin features and analytics."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import GLOBAL_CSS, APP_CSS
from database import get_admin_stats, block_user_trial

st.set_page_config(page_title="Admin Panel", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS, unsafe_allow_html=True)

# Security check
if not st.session_state.get("is_admin"):
    st.switch_page("Home.py")

st.markdown("""
<div class="hero-zone fade-up">
    <div class="hero-title">👑 Admin Control Panel</div>
    <div class="hero-sub">Manage users, view system analytics, and control access.</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-label">System Analytics</div>', unsafe_allow_html=True)
stats = get_admin_stats()

# Using your exact CSS classes for metrics so colors/fonts match perfectly
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="label">Total Users</div>
        <div class="value">{stats.get('total_users', 0)}</div>
        <div class="sub">Registered accounts</div>
    </div>
    <div class="metric-card">
        <div class="label">Pro Plan Users</div>
        <div class="value">{stats.get('plans', {}).get('pro', 0)}</div>
        <div class="sub">Paid subscriptions</div>
    </div>
    <div class="metric-card">
        <div class="label">Active Trials</div>
        <div class="value">{stats.get('plans', {}).get('free_trial', 0)}</div>
        <div class="sub">On 7-day access</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Access Control</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem;">
        <strong style="color: var(--text-primary); font-family: var(--font-body);">Block User Trial</strong><br>
        <span style="color: var(--text-muted); font-size: 0.85rem;">Instantly expire a user's free trial. They will be locked out until they purchase a plan.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_input, col_btn = st.columns([3, 1])
    
    with col_input:
        target_email = st.text_input("User Email Address", placeholder="user@domain.com", label_visibility="collapsed")
    
    with col_btn:
        if st.button("🚫 Block Access", use_container_width=True):
            if target_email:
                if block_user_trial(target_email):
                    st.success(f"✅ Access blocked for {target_email}.")
                else:
                    st.error("Failed to block user. Check database connection.")
            else:
                st.warning("Please enter an email address.")

st.divider()
if st.button("← Back to Portal"):
    st.switch_page("pages/4_Admin_Portal.py")
