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
    --accent-hover:  #00ffcc;
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

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Keep sidebar toggle visible (Do NOT hide collapsedControl) */

.block-container { padding: 2rem 2.5rem !important; max-width: 1200px; }
#MainMenu, footer, header { visibility: hidden; }

/* Hide specific internal elements without hiding the sidebar toggle */
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* Buttons */
.stButton > button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
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
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 20px #00d4aa40 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Section label */
.section-label {
    font-family: var(--font-body);
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.5rem 0 0.75rem 0;
    padding-left: 8px;
    border-left: 3px solid var(--accent);
}
</style>
"""

APP_CSS = """
<style>
.metric-card {
    background: var(--bg-card);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    border-left: 3px solid var(--accent);
}
.results-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}
</style>
"""
