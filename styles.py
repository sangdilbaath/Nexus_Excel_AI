"""Shared CSS styles for Nexus Excel AI."""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-primary:    #0d1117;
    --bg-secondary:  #161b22;
    --bg-card:       #1c2333;
    --border:        #30363d;
    --accent:        #00d4aa;
    --accent-dim:    #00d4aa22;
    --text-primary:  #e6edf3;
    --text-muted:    #8b949e;
    --danger:        #f85149;
    --warning:       #e3b341;
    --success:       #3fb950;
    --font-mono:     'Space Mono', monospace;
    --font-body:     'DM Sans', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}

/* ── Sidebar & Navigation Fixes ───────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
/* Force the sidebar collapse/expand button to be visible */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    color: var(--text-primary) !important;
}
[data-testid="stSidebarNavItems"], [data-testid="stSidebarNavSeparator"] { 
    display: none !important; 
}

/* ── UI Cleanup ───────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* Buttons */
.stButton > button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* CTA accent button */
.cta-btn > button {
    background: linear-gradient(135deg, #00d4aa, #0099ff) !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(0, 212, 170, 0.3) !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus { border-color: var(--accent) !important; }

/* Section labels */
.section-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.5rem 0 0.75rem 0;
    padding-left: 8px;
    border-left: 3px solid var(--accent);
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-up { animation: fadeUp 0.3s ease both; }
</style>
"""

APP_CSS = """
<style>
/* Dashboard Metrics */
.metric-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid var(--border);
    transition: transform 0.2s ease;
}
.metric-card:hover { transform: translateY(-3px); border-color: var(--accent); }
.metric-card .value { font-size: 1.5rem; font-weight: bold; color: var(--accent); }
.metric-card .label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }
</style>
"""
