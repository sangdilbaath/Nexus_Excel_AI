"""
pages/1_Pricing.py — Nexus Excel AI · Pricing Page
Shows 4 plan tiers; "Select Plan" → session_state → Billing page.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from styles import GLOBAL_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Pricing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }

/* Pricing grid */
.pricing-header {
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
    animation: fadeUp 0.35s ease both;
}
.pricing-header h2 {
    font-family: var(--font-mono);
    font-size: clamp(1.8rem, 4vw, 3rem);
    color: var(--text-primary);
    margin: 0 0 0.5rem 0;
}
.pricing-header h2 span { color: var(--accent); }
.pricing-header p { color: var(--text-muted); font-size: 1rem; max-width: 520px; margin: 0 auto; }

.plan-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem;
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    animation: fadeUp 0.4s ease 0.1s both;
    display: flex;
    flex-direction: column;
}
.plan-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px #00000050;
    border-color: var(--accent);
}
.plan-card.popular {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent), 0 8px 40px #00d4aa20;
}
.plan-badge {
    display: inline-block;
    background: var(--accent-dim);
    border: 1px solid #00d4aa44;
    color: var(--accent);
    font-size: 0.65rem;
    font-family: var(--font-mono);
    letter-spacing: 2px;
    text-transform: uppercase;
    border-radius: 12px;
    padding: 0.2rem 0.7rem;
    margin-bottom: 0.75rem;
}
.plan-name {
    font-family: var(--font-mono);
    font-size: 1.2rem;
    color: var(--text-primary);
    margin: 0 0 0.3rem 0;
}
.plan-price {
    font-family: var(--font-mono);
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--accent);
    margin: 0.5rem 0 0.25rem 0;
}
.plan-price .period { font-size: 0.9rem; font-weight: 400; color: var(--text-muted); }
.plan-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem; line-height: 1.5; }
.plan-features { list-style: none; padding: 0; margin: 0 0 1.5rem 0; flex-grow: 1; }
.plan-features li {
    font-size: 0.875rem;
    color: var(--text-primary);
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.plan-features li:last-child { border-bottom: none; }
.feat-yes { color: var(--success); font-size: 1rem; }
.feat-no  { color: var(--text-muted); font-size: 1rem; }
.feat-locked { color: var(--text-muted); font-size: 0.8rem; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ── Guard: must have email ────────────────────────────────────
if "email" not in st.session_state or not st.session_state["email"]:
    st.switch_page("Home.py")

email = st.session_state["email"]

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div class="pricing-header">
    <h2>Choose Your <span>Plan</span></h2>
    <p>Analysing data for <strong style="color:var(--text-primary)">{email}</strong>.
       All plans include the AI Data Analyst core.</p>
</div>
""", unsafe_allow_html=True)

# ── Plan definitions ──────────────────────────────────────────
PLANS = [
    {
        "key":     "free_trial",
        "name":    "Free Trial",
        "price":   "Free",
        "period":  "7 days",
        "desc":    "Full Pro access for one week. No credit card? You still enter simulated card details to start.",
        "badge":   "7-Day Trial",
        "popular": False,
        "features": [
            ("✅", "AI Chat Analysis"),
            ("✅", "Voice Commands"),
            ("✅", "Charts & Visualisations"),
            ("✅", "CSV / Excel Export"),
            ("⏳", "Expires after 7 days"),
        ],
    },
    {
        "key":     "basic",
        "name":    "Basic",
        "price":   "$9",
        "period":  "/month",
        "desc":    "Perfect for solo analysts who need fast text-based data querying.",
        "badge":   "Starter",
        "popular": False,
        "features": [
            ("✅", "AI Chat Analysis"),
            ("❌", "Voice Commands — locked"),
            ("❌", "Charts & Visualisations — locked"),
            ("✅", "CSV / Excel Export"),
            ("✅", "Up to 50 queries/session"),
        ],
    },
    {
        "key":     "premium",
        "name":    "Premium",
        "price":   "$29",
        "period":  "/month",
        "desc":    "Add voice input for hands-free analysis. Charts still coming with Pro.",
        "badge":   "Most Popular",
        "popular": True,
        "features": [
            ("✅", "AI Chat Analysis"),
            ("✅", "Voice Commands"),
            ("❌", "Charts & Visualisations — locked"),
            ("✅", "CSV / Excel Export"),
            ("✅", "Up to 50 queries/session"),
        ],
    },
    {
        "key":     "pro",
        "name":    "Pro",
        "price":   "$79",
        "period":  "/month",
        "desc":    "Full suite: chat, voice, and beautiful matplotlib charts on demand.",
        "badge":   "Full Power",
        "popular": False,
        "features": [
            ("✅", "AI Chat Analysis"),
            ("✅", "Voice Commands"),
            ("✅", "Charts & Visualisations"),
            ("✅", "CSV / Excel Export"),
            ("✅", "Up to 50 queries/session"),
        ],
    },
]

# ── Plan Cards ────────────────────────────────────────────────
cols = st.columns(4, gap="medium")

for col, plan in zip(cols, PLANS):
    with col:
        card_cls = "plan-card popular" if plan["popular"] else "plan-card"
        features_html = "".join([
            f'<li><span class="feat-{"yes" if icon == "✅" else "no"}">{icon}</span>{feat}</li>'
            for icon, feat in plan["features"]
        ])
        st.markdown(f"""
        <div class="{card_cls}">
            <div class="plan-badge">{plan["badge"]}</div>
            <div class="plan-name">{plan["name"]}</div>
            <div class="plan-price">{plan["price"]}<span class="period"> {plan["period"]}</span></div>
            <div class="plan-desc">{plan["desc"]}</div>
            <ul class="plan-features">{features_html}</ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        if st.button(f"Select {plan['name']}", key=f"plan_{plan['key']}", use_container_width=True):
            st.session_state["plan_selected"] = plan["key"]
            st.switch_page("pages/2_Billing.py")
        st.markdown('</div>', unsafe_allow_html=True)

# ── Back link ─────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, col_back, _ = st.columns([3, 1, 3])
with col_back:
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("Home.py")
