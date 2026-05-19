"""
Home.py — Nexus Excel AI · Landing Page
Entry point: email capture → redirect to Pricing or App.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, upsert_user, activate_plan, is_trial_expired
from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Home",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }

/* Landing-specific */
.hero-landing {
    text-align: center;
    padding: 5rem 1rem 3rem 1rem;
    animation: fadeUp 0.4s ease both;
}
.hero-badge {
    display: inline-block;
    background: var(--accent-dim);
    border: 1px solid #00d4aa44;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.75rem;
    color: var(--accent);
    font-family: var(--font-mono);
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
}
.hero-h1 {
    font-family: var(--font-mono);
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    color: var(--text-primary);
    line-height: 1.1;
    margin: 0 0 1rem 0;
}
.hero-h1 span { color: var(--accent); }
.hero-p {
    color: var(--text-muted);
    font-size: 1.15rem;
    max-width: 560px;
    margin: 0 auto 2.5rem auto;
    line-height: 1.7;
}
.email-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 8px 40px #00000040;
}
.email-card-title {
    font-family: var(--font-mono);
    font-size: 1rem;
    color: var(--text-primary);
    margin-bottom: 0.35rem;
}
.email-card-sub {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 1.25rem;
}

/* Feature strip */
.feature-strip {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    flex-wrap: wrap;
    margin: 4rem auto 2rem auto;
    max-width: 900px;
    padding: 0 1rem;
}
.feature-item {
    text-align: center;
    flex: 1;
    min-width: 160px;
    max-width: 220px;
    animation: fadeUp 0.4s ease 0.15s both;
}
.feature-icon { font-size: 2.2rem; margin-bottom: 0.75rem; }
.feature-title { font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.35rem; }
.feature-desc  { font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; }

/* Trusted bar */
.trust-bar {
    text-align: center;
    margin-top: 3rem;
    padding: 1.5rem;
    border-top: 1px solid var(--border);
}
.trust-bar p { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }
.trust-pills { display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; margin-top: 0.75rem; }
.trust-pill {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 1rem;
    font-size: 0.72rem;
    font-family: var(--font-mono);
    color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────
init_db()

# ── If already have email + paid → go straight to app ─────────
if st.session_state.get("user") and st.session_state["user"].get("has_payment_on_file"):
    st.switch_page("pages/3_App.py")

# ── Hero Section ──────────────────────────────────────────────
st.markdown("""
<div class="hero-landing">
    <div class="hero-badge">◈ Powered by Gemini 2.5</div>
    <h1 class="hero-h1">Your Spreadsheets,<br><span>Supercharged by AI.</span></h1>
    <p class="hero-p">
        Upload any CSV or Excel file and ask questions in plain English —
        or by voice. Nexus generates, runs, and explains Python analysis
        instantly.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Login / Master Key Section ────────────────────────────────
_, col_card, _ = st.columns([1, 1.6, 1])
with col_card:
    tab_user, tab_admin = st.tabs(["🚀 User Login", "👑 Master Key"])
    
    with tab_user:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Get started or Log in</div>
            <div class="email-card-sub">Enter your email to unlock your plan or resume your session.</div>
            <br>
        """, unsafe_allow_html=True)

        email_input = st.text_input(
            "email_field",
            placeholder="you@company.com",
            label_visibility="collapsed",
            key="user_email"
        )
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        go_btn = st.button("Continue  →", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if go_btn:
            raw = email_input.strip().lower()
            if "@" not in raw or "." not in raw.split("@")[-1]:
                st.error("Please enter a valid email address.")
            else:
                user = upsert_user(raw)
                st.session_state["email"] = raw
                st.session_state["user"]  = user

                # ── CRITICAL FIX: Direct returning active users to the App
                if user.get("has_payment_on_file"):
                    if not is_trial_expired(user):
                        st.switch_page("pages/3_App.py")

                # If new user or expired trial, go to pricing
                st.switch_page("pages/1_Pricing.py")

    with tab_admin:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Admin Access</div>
            <div class="email-card-sub">Strictly restricted to authorized administrator. Bypasses all limits.</div>
            <br>
        """, unsafe_allow_html=True)
        
        admin_email = st.text_input("Admin Email", placeholder="admin@domain.com", key="admin_email")
        admin_pass = st.text_input("Password", type="password", key="admin_pass")

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        admin_btn = st.button("Unlock Dashboard  →", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if admin_btn:
            if admin_email.strip().lower() == "sangdilsingh62@gmail.com" and admin_pass == "1322":
                upsert_user(admin_email)
                # Force activation of max plan
                admin_user = activate_plan(admin_email, "pro")
                st.session_state["email"] = admin_email
                st.session_state["user"] = admin_user
                st.session_state["is_admin"] = True
                
                st.success("✅ Master Key Accepted! Booting Dashboard...")
                time.sleep(1.2)
                st.switch_page("pages/3_App.py")
            else:
                st.error("❌ Access Denied: Unrecognized email or incorrect password.")

# ── Feature Strip ─────────────────────────────────────────────
st.markdown("""
<div class="feature-strip">
    <div class="feature-item">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">AI Data Analyst</div>
        <div class="feature-desc">Ask anything. Gemini 2.5 writes and runs the Python for you.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">🎙️</div>
        <div class="feature-title">Voice Commands</div>
        <div class="feature-desc">Speak your analysis — microphone input with instant transcription.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Instant Charts</div>
        <div class="feature-desc">Ask for a bar, line, or scatter chart — rendered in seconds.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Zero Setup</div>
        <div class="feature-desc">Upload CSV or Excel, type your question. That's it.</div>
    </div>
</div>

<div class="trust-bar">
    <p>Trusted features</p>
    <div class="trust-pills">
        <span class="trust-pill">SQLite Auth</span>
        <span class="trust-pill">Feature Gating</span>
        <span class="trust-pill">Trial Management</span>
        <span class="trust-pill">Secure Exec Engine</span>
        <span class="trust-pill">Export CSV / Excel</span>
    </div>
</div>
""", unsafe_allow_html=True)
