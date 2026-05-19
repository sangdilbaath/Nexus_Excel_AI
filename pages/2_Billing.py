"""
pages/2_Billing.py — Nexus Excel AI · Billing & Checkout
Simulated checkout form; on success updates DB and redirects to app.
"""

import streamlit as st
import sys, os, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import activate_plan, PLAN_LABELS
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

.checkout-wrap {
    max-width: 540px;
    margin: 2rem auto;
    animation: fadeUp 0.35s ease both;
}
.checkout-header {
    text-align: center;
    margin-bottom: 2rem;
}
.checkout-header .lock-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.checkout-header h2 {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    color: var(--text-primary);
    margin: 0 0 0.35rem 0;
}
.checkout-header p { color: var(--text-muted); font-size: 0.9rem; }

/* Order summary */
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
.order-label { font-family: var(--font-body); }
.order-value { font-family: var(--font-mono); color: var(--accent); }

/* Form card */
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
.ssl-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 1rem;
}
.ssl-badge .lock { color: var(--success); }

/* Card brand row */
.card-brands {
    display: flex;
    gap: 0.4rem;
    margin: 0.5rem 0 1rem 0;
}
.card-brand-pill {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.15rem 0.5rem;
    font-size: 0.7rem;
    font-family: var(--font-mono);
    color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)

# ── Guards ────────────────────────────────────────────────────
if "email" not in st.session_state or not st.session_state.get("email"):
    st.switch_page("Home.py")
if "plan_selected" not in st.session_state or not st.session_state.get("plan_selected"):
    st.switch_page("pages/1_Pricing.py")

email        = st.session_state["email"]
plan_key     = st.session_state["plan_selected"]
plan_label   = PLAN_LABELS.get(plan_key, plan_key.replace("_", " ").title())

PLAN_PRICES = {
    "free_trial": "$0.00",
    "basic":      "$9.00 / month",
    "premium":    "$29.00 / month",
    "pro":        "$79.00 / month",
}

# ── Layout ────────────────────────────────────────────────────
st.markdown('<div class="checkout-wrap">', unsafe_allow_html=True)

st.markdown(f"""
<div class="checkout-header">
    <div class="lock-icon">🔒</div>
    <h2>Secure Checkout</h2>
    <p>Complete your payment to activate your <strong style="color:var(--accent)">{plan_label}</strong> plan.</p>
</div>
""", unsafe_allow_html=True)

# Order summary
st.markdown(f"""
<div class="order-box">
    <div class="order-row">
        <span class="order-label">Plan</span>
        <span class="order-value">{plan_label}</span>
    </div>
    <div class="order-row">
        <span class="order-label">Email</span>
        <span class="order-value" style="font-size:0.8rem;">{email}</span>
    </div>
    <div class="order-row">
        <span class="order-label">Total</span>
        <span class="order-value">{PLAN_PRICES.get(plan_key, "—")}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Checkout form ─────────────────────────────────────────────
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

st.markdown('<div class="ssl-badge"><span class="lock">🔒</span> 256-bit SSL encrypted · Simulated payment for demo</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)  # close form-card

st.markdown("<br>", unsafe_allow_html=True)

# ── Validation helpers ─────────────────────────────────────────
def _clean_card(s: str) -> str:
    return re.sub(r"\D", "", s)

def _validate_form() -> list[str]:
    errors = []
    if not cardholder_name.strip():
        errors.append("Cardholder name is required.")
    raw_card = _clean_card(card_number)
    if len(raw_card) < 13 or len(raw_card) > 19:
        errors.append("Card number must be 13–19 digits.")
    raw_exp = re.sub(r"[\s/]", "", expiry)
    if not re.fullmatch(r"\d{4}", raw_exp):
        errors.append("Expiry must be MM/YY format.")
    else:
        month, year = int(raw_exp[:2]), int(raw_exp[2:]) + 2000
        if not (1 <= month <= 12):
            errors.append("Expiry month must be 01–12.")
    raw_cvv = cvv.strip()
    if not re.fullmatch(r"\d{3,4}", raw_cvv):
        errors.append("CVV must be 3 or 4 digits.")
    return errors

# ── Submit button ─────────────────────────────────────────────
st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
pay_btn = st.button("💳  Complete Payment & Activate Plan", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if pay_btn:
    errors = _validate_form()
    if errors:
        for err in errors:
            st.error(f"⚠️ {err}")
    else:
        with st.spinner("Processing payment…"):
            time.sleep(1.5)  # simulate network call

        # Update DB
        updated_user = activate_plan(email, plan_key)
        st.session_state["user"] = updated_user

        st.success(f"✅ Payment accepted! Your **{plan_label}** plan is now active.")
        time.sleep(1.2)
        st.switch_page("pages/3_App.py")

st.markdown("<br>", unsafe_allow_html=True)
col_back, _ = st.columns([1, 3])
with col_back:
    if st.button("← Change Plan"):
        st.switch_page("pages/1_Pricing.py")

st.markdown('</div>', unsafe_allow_html=True)  # close checkout-wrap
