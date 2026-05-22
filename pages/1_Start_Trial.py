"""
pages/1_Start_Trial.py — Nexus Excel AI · Start Trial
Simple one-click activation for the 2-day free trial.
"""

import streamlit as st
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import activate_plan, has_used_trial
from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Start Trial",
    page_icon="🎁",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.trial-wrap { max-width: 500px; margin: 3rem auto; animation: fadeUp 0.35s ease both; text-align: center; }
.trial-card {
    background: var(--bg-card);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 40px #00d4aa15;
}
.blocked-card {
    background: var(--bg-card);
    border: 1px solid var(--danger);
    border-radius: 16px;
    padding: 2.5rem 2rem;
}
.trial-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.trial-email-box {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: var(--font-mono);
    font-size: 0.95rem;
    color: var(--text-primary);
    margin: 1.5rem 0;
    word-break: break-all;
}
</style>
""", unsafe_allow_html=True)

# ── Guards ────────────────────────────────────────────────────
if "email" not in st.session_state or not st.session_state["email"]:
    st.switch_page("Home.py")

email = st.session_state["email"]

st.markdown('<div class="trial-wrap">', unsafe_allow_html=True)

if has_used_trial(email):
    # ── BLOCKED FLOW ──────────────────────────────────────────
    st.markdown(f"""
    <div class="blocked-card">
        <div class="trial-icon">🚫</div>
        <h3 style="color:var(--danger); font-family:var(--font-mono); margin-bottom: 0.5rem;">Trial Already Used</h3>
        <p style="color:var(--text-muted); font-size: 0.95rem; line-height: 1.6;">
            The email account below has already claimed a free trial.
        </p>
        <div class="trial-email-box">{email}</div>
        <p style="color:var(--text-muted); font-size: 0.9rem;">
            Please contact support to continue using Nexus.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Home", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Home.py")

else:
    # ── START TRIAL FLOW ──────────────────────────────────────
    st.markdown(f"""
    <div class="trial-card">
        <div class="trial-icon">🎁</div>
        <h3 style="color:var(--accent); font-family:var(--font-mono); margin-bottom: 0.5rem;">Start Free Trial</h3>
        <p style="color:var(--text-muted); font-size: 0.95rem; line-height: 1.6;">
            Instantly unlock all Nexus Pro features for 2 full days. No credit card required.
        </p>
        <div class="trial-email-box">{email}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    start_btn = st.button("🚀 Start Free Trial", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if start_btn:
        with st.spinner("Activating your trial…"):
            try:
                updated_user = activate_plan(email, "trial")
            except Exception:
                updated_user = None
                
            if not updated_user:
                # Updated to use expiry_date and a 2-day limit
                expiry = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
                updated_user = {
                    "email": email, 
                    "plan_type": "trial", 
                    "has_payment_on_file": 1, 
                    "expiry_date": expiry
                }
            
            st.session_state["user"] = updated_user
        
        st.success("✅ Trial activated! Redirecting to your dashboard…")
        time.sleep(1.2)
        st.switch_page("pages/3_App.py")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Use a different email", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Home.py")

st.markdown('</div>', unsafe_allow_html=True)
