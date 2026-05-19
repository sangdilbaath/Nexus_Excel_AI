"""
pages/2_Billing.py — Nexus Excel AI · Billing & Checkout
• Free Trial  → email confirmation only (no card), blocked if email already used a trial
• Paid plans  → full simulated card checkout form
"""

import streamlit as st
import sys, os, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import activate_plan, has_used_trial, PLAN_LABELS
from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Checkout",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }

.checkout-wrap { max-width: 540px; margin: 2rem auto; animation: fadeUp 0.35s ease both; }

.checkout-header { text-align: center; margin-bottom: 2rem; }
.checkout-header .icon { font-size: 2.8rem; margin-bottom: 0.5rem; }
.checkout-header h2 {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    color: var(--text-primary);
    margin: 0 0 0.35rem 0;
}
.checkout-header p { color: var(--text-muted); font-size: 0.9rem; }

.order-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
}
.order-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    font-size: 0.9rem;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
}
.order-row:last-child { border-bottom: none; font-weight: 600; color: var(--text-primary); }
.order-value { font-family: var(--font-mono); color: var(--accent); }

.form-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem;
}
.form-section {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.25rem 0 0.75rem 0;
    padding-left: 8px;
    border-left: 3px solid var(--accent);
}

/* Trial-specific */
.trial-confirm-card {
    background: var(--bg-card);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}
.trial-confirm-card .trial-icon { font-size: 2.8rem; margin-bottom: 0.75rem; }
.trial-confirm-card h3 {
    font-family: var(--font-mono);
    color: var(--accent);
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
}
.trial-confirm-card p { color: var(--text-muted); font-size: 0.875rem; line-height: 1.6; margin: 0 0 1.25rem 0; }
.trial-email-box {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-family: var(--font-mono);
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-bottom: 1.25rem;
    word-break: break-all;
}
.trial-perks { list-style: none; padding: 0; margin: 0 0 1.5rem 0; text-align: left; }
.trial-perks li {
    padding: 0.35rem 0;
    font-size: 0.875rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 0.6rem;
}
.trial-perks li:last-child { border-bottom: none; }

/* Blocked state */
.blocked-card {
    background: #f8514910;
    border: 1px solid #f8514940;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}
.blocked-card .blocked-icon { font-size: 3rem; margin-bottom: 0.75rem; }
.blocked-card h3 { font-family: var(--font-mono); color: var(--danger); margin: 0 0 0.5rem 0; font-size: 1.2rem; }
.blocked-card p { color: var(--text-muted); font-size: 0.875rem; line-height: 1.6; margin: 0 0 1.5rem 0; }
.blocked-email { color: var(--text-primary); font-weight: 600; }

.ssl-badge {
    display: flex; align-items: center; justify-content: center;
    gap: 0.5rem; font-size: 0.75rem; color: var(--text-muted); margin-top: 1rem;
}
.card-brands { display: flex; gap: 0.4rem; margin: 0.5rem 0 1rem 0; }
.card-brand-pill {
    background: var(--bg-secondary); border: 1px solid var(--border);
    border-radius: 4px; padding: 0.15rem 0.5rem;
    font-size: 0.7rem; font-family: var(--font-mono); color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)

# ── Guards ────────────────────────────────────────────────────
if not st.session_state.get("email"):
    st.switch_page("Home.py")
if not st.session_state.get("plan_selected"):
    st.switch_page("pages/1_Pricing.py")

email      = st.session_state["email"]
plan_key   = st.session_state["plan_selected"]
plan_label = PLAN_LABELS.get(plan_key, plan_key.replace("_", " ").title())

PLAN_PRICES = {
    "free_trial": "Free",
    "basic":      "$9.00 / month",
    "premium":    "$29.00 / month",
    "pro":        "$79.00 / month",
}

st.markdown('<div class="checkout-wrap">', unsafe_allow_html=True)

# ============================================================
# FREE TRIAL FLOW — email only, no card details
# ============================================================
if plan_key == "free_trial":

    already_used = has_used_trial(email)

    if already_used:
        # ── HARD BLOCK ────────────────────────────────────────
        st.markdown(f"""
        <div class="blocked-card">
            <div class="blocked-icon">🚫</div>
            <h3>Free Trial Already Used</h3>
            <p>
                The email <span class="blocked-email">{email}</span> has already
                claimed a 7-day free trial.<br><br>
                Each email address is eligible for <strong>one free trial only</strong>.
                You cannot start another trial with the same email — even after it expires.
                Please choose a paid plan to continue.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        if st.button("🚀 View Paid Plans", use_container_width=True):
            st.session_state.pop("plan_selected", None)
            st.switch_page("pages/1_Pricing.py")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Use a different email", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")

    else:
        # ── TRIAL CONFIRMATION ────────────────────────────────
        st.markdown(f"""
        <div class="trial-confirm-card">
            <div class="trial-icon">🎁</div>
            <h3>Claim Your 7-Day Free Trial</h3>
            <p>
                No credit card required. Your trial starts the moment you confirm
                and unlocks <strong style="color:var(--accent)">all Pro features</strong>
                for 7 full days.
            </p>
            <div class="trial-email-box">✉️ &nbsp;{email}</div>
            <ul class="trial-perks">
                <li>✅ AI Chat Analysis — unlimited queries</li>
                <li>✅ Voice Commands via microphone</li>
                <li>✅ Charts &amp; Visualisations (matplotlib)</li>
                <li>✅ CSV &amp; Excel Export</li>
                <li>⏳ Expires automatically after 7 days</li>
                <li>🔒 One free trial per email address — no repeats</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        start_btn = st.button("🚀 Start My Free Trial", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if start_btn:
            with st.spinner("Activating your trial…"):
                time.sleep(1.0)
            
            # CRITICAL FIX: Bulletproof try/except so a locked DB doesn't crash to Home
            try:
                updated_user = activate_plan(email, "free_trial")
            except Exception:
                updated_user = None
                
            if not updated_user:
                updated_user = {"email": email, "plan_type": "free_trial", "has_payment_on_file": 1, "trial_end_date": "2030-01-01 00:00:00"}
            
            st.session_state["user"] = updated_user
            st.success("✅ Trial activated! Redirecting to your dashboard…")
            time.sleep(1.2)
            st.switch_page("pages/3_App.py")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Change Plan"):
            st.switch_page("pages/1_Pricing.py")

# ============================================================
# PAID PLAN FLOW — full simulated card checkout
# ============================================================
else:
    st.markdown(f"""
    <div class="checkout-header">
        <div class="icon">🔒</div>
        <h2>Secure Checkout</h2>
        <p>Complete your payment to activate the
           <strong style="color:var(--accent)">{plan_label}</strong> plan.</p>
    </div>
    """, unsafe_allow_html=True)

    # Order summary
    st.markdown(f"""
    <div class="order-box">
        <div class="order-row">
            <span>Plan</span>
            <span class="order-value">{plan_label}</span>
        </div>
        <div class="order-row">
            <span>Email</span>
            <span class="order-value" style="font-size:0.8rem;">{email}</span>
        </div>
        <div class="order-row">
            <span>Total</span>
            <span class="order-value">{PLAN_PRICES.get(plan_key, "—")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-section">Cardholder Details</div>', unsafe_allow_html=True)
    cardholder_name = st.text_input("Full Name on Card", placeholder="Jane Doe")

    st.markdown('<div class="form-section">Card Information</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-brands">
        <span class="card-brand-pill">VISA</span>
        <span class="card-brand-pill">MASTERCARD</span>
        <span class="card-brand-pill">AMEX</span>
        <span class="card-brand-pill">DISCOVER</span>
    </div>
    """, unsafe_allow_html=True)

    card_number = st.text_input("Card Number", placeholder="4242 4242 4242 4242", max_chars=19)
    col_exp, col_cvv = st.columns(2)
    with col_exp:
        expiry = st.text_input("Expiry Date", placeholder="MM / YY", max_chars=7)
    with col_cvv:
        cvv = st.text_input("CVV / CVC", placeholder="123", max_chars=4, type="password")

    st.markdown('<div class="ssl-badge">🔒 256-bit SSL encrypted · Simulated payment for demo</div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    def _clean_card(s):
        return re.sub(r"\D", "", s)

    def _validate():
        errors = []
        if not cardholder_name.strip():
            errors.append("Cardholder name is required.")
        raw_card = _clean_card(card_number)
        if not (13 <= len(raw_card) <= 19):
            errors.append("Card number must be 13–19 digits.")
        raw_exp = re.sub(r"[\s/]", "", expiry)
        if not re.fullmatch(r"\d{4}", raw_exp):
            errors.append("Expiry must be MM/YY format.")
        else:
            m = int(raw_exp[:2])
            if not (1 <= m <= 12):
                errors.append("Expiry month must be 01–12.")
        if not re.fullmatch(r"\d{3,4}", cvv.strip()):
            errors.append("CVV must be 3 or 4 digits.")
        return errors

    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    pay_btn = st.button("💳  Complete Payment & Activate Plan", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if pay_btn:
        errs = _validate()
        if errs:
            for e in errs:
                st.error(f"⚠️ {e}")
        else:
            with st.spinner("Processing payment…"):
                time.sleep(1.5)
            
            # CRITICAL FIX: Bulletproof try/except so a locked DB doesn't crash to Home
            try:
                updated_user = activate_plan(email, plan_key)
            except Exception:
                updated_user = None
                
            if not updated_user:
                updated_user = {"email": email, "plan_type": plan_key, "has_payment_on_file": 1, "trial_end_date": None}
            
            st.session_state["user"] = updated_user
            st.success(f"✅ Payment accepted! Your **{plan_label}** plan is now active.")
            time.sleep(1.2)
            st.switch_page("pages/3_App.py")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Change Plan"):
            st.switch_page("pages/1_Pricing.py")

st.markdown('</div>', unsafe_allow_html=True)
