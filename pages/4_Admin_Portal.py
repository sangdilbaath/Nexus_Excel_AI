"""pages/4_Admin_Portal.py — Admin routing hub."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import GLOBAL_CSS

st.set_page_config(page_title="Admin Portal", page_icon="👑", layout="centered", initial_sidebar_state="collapsed")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Security check
if not st.session_state.get("is_admin"):
    st.switch_page("Home.py")

st.markdown("""
<div style="text-align:center; padding: 4rem 1rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">👑</div>
    <h2 style="font-family: var(--font-mono); color: var(--text-primary);">Master Key Portal</h2>
    <p style="color: var(--text-muted);">Select your destination.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    if st.button("📊 Admin Panel", use_container_width=True):
        st.switch_page("pages/5_Admin_Panel.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    if st.button("🤖 Use AI (Dashboard)", use_container_width=True):
        st.switch_page("pages/3_App.py")
    st.markdown('</div>', unsafe_allow_html=True)
