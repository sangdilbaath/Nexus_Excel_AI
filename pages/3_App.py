"""
pages/3_App.py — Nexus Excel AI · Main AI Dashboard
Access-controlled, feature-gated AI data analyst powered by Gemini 2.5.
"""

import streamlit as st
import sys, os, re, io, time, datetime, concurrent.futures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from database import init_db, is_trial_expired, days_remaining, PLAN_LABELS
from styles import GLOBAL_CSS, APP_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS,    unsafe_allow_html=True)

init_db()

# ============================================================
# ACCESS CONTROL
# ============================================================
is_admin = st.session_state.get("is_admin", False)

if is_admin:
    # Completely bypass all database and payment checks for the Master Key
    user = st.session_state.get("user", {
        "email": "sangdilsingh62@gmail.com",
        "plan_type": "pro",
        "has_payment_on_file": 1,
        "trial_end_date": None
    })
    plan = "pro"
    trial_exp = False
else:
    user = st.session_state.get("user")
    
    # No user at all → back to home
    if not user:
        st.switch_page("Home.py")

    # Refresh user from DB (in case page was reloaded)
    from database import get_user
    email = st.session_state.get("email", user.get("email", ""))
    if email:
        fresh = get_user(email)
        if fresh:
            user = fresh
            st.session_state["user"] = fresh

    # Not paid → billing
    if not user.get("has_payment_on_file"):
        st.switch_page("pages/2_Billing.py")

    plan       = user.get("plan_type", "none")
    trial_exp  = is_trial_expired(user)

# ── Trial expiry wall ─────────────────────────────────────────
if trial_exp:
    st.markdown("""
    <div style="text-align:center; padding:5rem 1rem;">
        <div style="font-size:3rem;">⏰</div>
        <h2 style="font-family:'Space Mono',monospace; color:#e6edf3; margin:1rem 0 0.5rem 0;">
            Your Free Trial Has Expired
        </h2>
        <p style="color:#8b949e; font-size:1rem; max-width:460px; margin:0 auto 2rem auto;">
            Your 7-day trial ended. Upgrade to a paid plan to continue using Nexus Excel AI.
        </p>
    </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([2, 1, 2])
    with col_btn:
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        if st.button("🚀 Upgrade My Plan", use_container_width=True):
            st.session_state.pop("plan_selected", None)
            st.switch_page("pages/1_Pricing.py")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Feature flags from plan ────────────────────────────────────
VOICE_ENABLED  = plan in ("free_trial", "premium", "pro") or is_admin
CHART_ENABLED  = plan in ("free_trial", "pro") or is_admin

# ============================================================
# CONSTANTS
# ============================================================
MAX_FILE_SIZE_MB         = 10
# Unlimited requests for admin
MAX_REQUESTS_PER_SESSION = 99999 if is_admin else 50
AI_TIMEOUT_SECONDS       = 30
PYTHON_KEYWORDS          = {'import', 'def', 'df', 'plt', 'pd', 'for', 'if', 'print', 'return', '=', 'fig', 'ax'}

# ============================================================
# SESSION STATE
# ============================================================
for key, default in {
    "query_text":      "",
    "updated_df":      None,
    "chart_gallery":   [],
    "command_history": [],
    "df":              None,
    "last_filename":   None,
    "show_all_data":   False,
    "show_all_cols":   False,
    "request_count":   0,
    "is_recording":    False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# HELPERS
# ============================================================
def clean_ai_code(raw: str) -> str:
    raw = re.sub(r"`{3}(?:python)?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"`{3}", "", raw)
    return raw.strip()

def is_likely_python(code: str) -> bool:
    return any(kw in code for kw in PYTHON_KEYWORDS)

def sanitize_col_name(name: str) -> str:
    return re.sub(r"[^\w\s\-\.]", "_", str(name))

def get_df_summary(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        safe_col = sanitize_col_name(col)
        dtype    = str(df[col].dtype)
        nulls    = int(df[col].isnull().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            desc  = df[col].describe()
            stats = f"min={desc['min']:.2f}, max={desc['max']:.2f}, mean={desc['mean']:.2f}"
        else:
            top5  = df[col].dropna().astype(str).value_counts().head(5).index.tolist()
            stats = "top values: " + ", ".join(top5)
        lines.append(f"- `{safe_col}` ({dtype}, {nulls} nulls) → {stats}")
    return "\n".join(lines)

def render_metrics(df: pd.DataFrame):
    num_cols    = df.select_dtypes(include='number').shape[1]
    missing_pct = round(df.isnull().mean().mean() * 100, 1)
    mem_kb      = round(df.memory_usage(deep=True).sum() / 1024, 1)
    mem_unit    = "KB" if mem_kb < 1024 else "MB"
    mem_val     = mem_kb if mem_kb < 1024 else round(mem_kb / 1024, 2)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Rows</div>
            <div class="value">{df.shape[0]:,}</div>
            <div class="sub">records</div>
        </div>
        <div class="metric-card">
            <div class="label">Columns</div>
            <div class="value">{df.shape[1]}</div>
            <div class="sub">{num_cols} numeric</div>
        </div>
        <div class="metric-card">
            <div class="label">Missing</div>
            <div class="value">{missing_pct}<span class="unit">%</span></div>
            <div class="sub">null values</div>
        </div>
        <div class="metric-card">
            <div class="label">Memory</div>
            <div class="value">{mem_val}<span class="unit">{mem_unit}</span></div>
            <div class="sub">in use</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name
    if name.endswith('.csv'):
        raw = uploaded_file.read()
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=enc, parse_dates=True)
                break
            except Exception:
                continue
        else:
            raise ValueError("Could not decode CSV.")
    else:
        df = pd.read_excel(uploaded_file, parse_dates=True)
        if df.columns.duplicated().any() or df.columns.isnull().any():
            st.warning(
                "Merged or unnamed header cells detected. "
                "Consider un-merging header rows in Excel before uploading.",
                icon="⚠️",
            )
    for col in df.select_dtypes(include='object').columns:
        try:
            converted = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
            if converted.notna().sum() / max(len(df), 1) > 0.7:
                df[col] = converted
        except Exception:
            pass
    return df

def call_gemini_with_timeout(client, prompt: str, timeout: int = AI_TIMEOUT_SECONDS) -> str:
    def _call():
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        ).text
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_call)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Gemini API did not respond within {timeout}s.")

def trim_memory():
    if len(st.session_state.command_history) > 50:
        st.session_state.command_history = st.session_state.command_history[-50:]
    if len(st.session_state.chart_gallery) > 10:
        st.session_state.chart_gallery = st.session_state.chart_gallery[-10:]

# ============================================================
# SIDEBAR
# ============================================================
plan_label = PLAN_LABELS.get(plan, plan)
trial_days = days_remaining(user) if plan == "free_trial" else None

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo">◈ NEXUS</div>
        <div class="tagline">Excel AI · Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Master Key Badge
    if is_admin:
        st.markdown("""
        <div style="background:#f8514915; border:1px solid #f8514950; border-radius:8px;
                    padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
            <span style="font-size:0.75rem; color:#f85149; text-transform:uppercase; letter-spacing:1px; font-weight:700;">
                👑 Master Key Active
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Plan badge
    plan_color = {"free_trial": "#e3b341", "basic": "#8b949e", "premium": "#0099ff", "pro": "#00d4aa"}.get(plan, "#8b949e")
    trial_info = f" · {trial_days}d left" if trial_days is not None else ""
    st.markdown(f"""
    <div style="background:#1c2333; border:1px solid #30363d; border-radius:8px;
                padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
        <span style="font-size:0.72rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Active Plan</span><br>
        <span style="font-family:'Space Mono',monospace; color:{plan_color}; font-weight:700;">{plan_label}{trial_info}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza…")

    st.markdown('<div class="section-label">Session Controls</div>', unsafe_allow_html=True)
    if st.button("🗑️ Reset Session", use_container_width=True):
        for key in ["updated_df", "chart_gallery", "query_text",
                    "command_history", "df", "last_filename",
                    "show_all_data", "show_all_cols", "request_count"]:
            st.session_state[key] = (
                []    if key in ("command_history", "chart_gallery") else
                ""    if key == "query_text" else
                0     if key == "request_count" else
                False if key in ("show_all_data", "show_all_cols") else
                None
            )
        st.rerun()

    if st.button("🔄 Change Plan", use_container_width=True):
        st.session_state.pop("plan_selected", None)
        st.switch_page("pages/1_Pricing.py")

    # Audit trail
    if st.session_state.command_history:
        st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
        with st.expander(f"📝 {len(st.session_state.command_history)} command(s)", expanded=False):
            for entry in reversed(st.session_state.command_history):
                badge   = '<span class="audit-badge-ok">✓ OK</span>'   if entry["ok"] \
                     else '<span class="audit-badge-err">✗ Fail</span>'
                rows_info = ""
                if entry.get("rows_before") is not None:
                    rows_info = f'· {entry["rows_before"]:,} → {entry["rows_after"]:,} rows'
                st.markdown(f"""
                <div class="audit-item">
                    <div class="audit-cmd">{entry["cmd"]}</div>
                    <div class="audit-meta">{badge}<span>{entry["ts"]}</span><span>{rows_info}</span></div>
                </div>
                """, unsafe_allow_html=True)

    remaining = MAX_REQUESTS_PER_SESSION - st.session_state.request_count
    
    if is_admin:
        limit_text = "◈ Unlimited requests"
    else:
        limit_text = f"◈ {remaining}/{MAX_REQUESTS_PER_SESSION} requests left"
        
    st.markdown(f'<div class="rate-limit-badge">{limit_text}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="background:#1c2333; border:1px solid #30363d; border-radius:8px;
                padding:0.7rem 1rem; text-align:center;">
        <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">
            Nexus v3.2 · 2026 Pro
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero-zone fade-up">
    <div class="hero-title">◈ NEXUS Excel AI</div>
    <div class="hero-sub">Professional Spreadsheet Intelligence Engine</div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
    <div style="background:#1c2333; border:1px solid #30363d; border-radius:12px;
                padding:2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔑</div>
        <div style="font-family:'Space Mono',monospace; color:#e6edf3; font-size:1rem;">API Key Required</div>
        <div style="color:#8b949e; font-size:0.875rem; margin-top:0.4rem;">
            Enter your Gemini API Key in the sidebar to activate the engine.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
# MAIN CONTENT
# ============================================================
try:
    from google import genai
    client = genai.Client(api_key=api_key)

    # ── File Upload ──────────────────────────────────────────
    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload spreadsheet",
        type=["xlsx", "csv"],
        label_visibility="collapsed",
        help="Supported: .csv and .xlsx · Max 10 MB",
    )

    if uploaded_file is None:
        st.markdown("""
        <div style="background:#1c2333; border:2px dashed #30363d; border-radius:12px;
                    padding:3rem; text-align:center; margin-top:1rem;">
            <div style="font-size:2.5rem;">📂</div>
            <div style="font-family:'Space Mono',monospace; color:#8b949e; margin-top:0.5rem;">
                Drop a CSV or XLSX file above to get started
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(
            f"❌ File too large ({round(uploaded_file.size/1024/1024, 1)} MB). "
            f"Maximum allowed is {MAX_FILE_SIZE_MB} MB.",
            icon="🚫",
        )
        st.stop()

    if uploaded_file.name != st.session_state.last_filename:
        with st.spinner("Loading file…"):
            st.session_state.df              = load_file(uploaded_file)
            st.session_state.last_filename   = uploaded_file.name
            st.session_state.updated_df      = None
            st.session_state.chart_gallery   = []
            st.session_state.command_history = []
            st.session_state.request_count   = 0

    current_df = (
        st.session_state.updated_df
        if st.session_state.updated_df is not None
        else st.session_state.df
    )

    # ── Dataset Overview ──────────────────────────────────────
    st.markdown('<div class="section-label">Dataset Overview</div>', unsafe_allow_html=True)
    render_metrics(current_df)

    # Column pills
    pills_html = "".join([f'<span class="col-pill">{sanitize_col_name(c)}</span>' for c in current_df.columns])
    wrap_cls   = "col-pills-wrap" + (" expanded" if st.session_state.show_all_cols else "")
    st.markdown(f'<div class="{wrap_cls}">{pills_html}</div>', unsafe_allow_html=True)
    if st.button("▾ Show all columns" if not st.session_state.show_all_cols else "▴ Collapse columns", key="toggle_cols"):
        st.session_state.show_all_cols = not st.session_state.show_all_cols
        st.rerun()

    # Data preview
    col_title, col_toggle = st.columns([5, 1])
    with col_title:
        st.markdown('<div class="section-label">Data Preview</div>', unsafe_allow_html=True)
    with col_toggle:
        label = "🔼 Less" if st.session_state.show_all_data else "🔽 More"
        if st.button(label, use_container_width=True):
            st.session_state.show_all_data = not st.session_state.show_all_data
            st.rerun()

    preview_df = current_df if st.session_state.show_all_data else current_df.head(5)
    st.dataframe(preview_df, use_container_width=True, height=220)

    # ── Command Interface ──────────────────────────────────────
    st.markdown('<div class="section-label">Command Interface</div>', unsafe_allow_html=True)

    # Feature-gate banners
    if not VOICE_ENABLED:
        st.markdown("""
        <div class="gate-banner">
            🔒 <strong>Voice Input</strong> — Upgrade to Premium or Pro to unlock microphone commands.
        </div>
        """, unsafe_allow_html=True)
    if not CHART_ENABLED:
        st.markdown("""
        <div class="gate-banner">
            🔒 <strong>Charts & Visualisations</strong> — Upgrade to Pro or Free Trial to unlock matplotlib charts.
        </div>
        """, unsafe_allow_html=True)

    col_mic, col_txt = st.columns([1, 6])
    with col_mic:
        if VOICE_ENABLED:
            try:
                from streamlit_mic_recorder import speech_to_text
                text_from_voice = speech_to_text(
                    language='en',
                    start_prompt="🎙️",
                    stop_prompt="🛑 Stop",
                    just_once=True,
                    key='nexus_stt',
                )
                if text_from_voice:
                    st.session_state.query_text = text_from_voice
                    st.session_state.is_recording = False
                if st.session_state.get("is_recording"):
                    st.markdown('<div class="recording-indicator"><span class="pulse-dot"></span> Listening…</div>',
                                unsafe_allow_html=True)
            except ImportError:
                st.button("🎙️", disabled=True, help="Install streamlit-mic-recorder")
        else:
            st.button("🔒", disabled=True, help="Upgrade to Premium/Pro for voice input")

    with col_txt:
        final_query = st.text_area(
            "command_input",
            value=st.session_state.query_text,
            placeholder="e.g., 'Bar chart of Sales by Region' or 'Add a profit margin column'",
            label_visibility="collapsed",
            height=80,
        )

    # Rate limit
    if st.session_state.request_count >= MAX_REQUESTS_PER_SESSION and not is_admin:
        st.warning(f"⚠️ Session limit of {MAX_REQUESTS_PER_SESSION} requests reached. Reset the session to continue.")
    else:
        col_exec, _ = st.columns([2, 5])
        with col_exec:
            st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
            execute_btn = st.button("▶  Execute Command", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if execute_btn and final_query.strip():
            df_summary  = get_df_summary(current_df)
            rows_before = len(current_df)

            # ── Build chart rule based on plan ───────────────
            if CHART_ENABLED:
                chart_rule = (
                    "3. CHART TASKS: Never overwrite 'df'. Use matplotlib. End EVERY chart with:\n"
                    "   plt.tight_layout()\n"
                    "   plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#1c2333')\n"
                    "   plt.close()\n"
                    "4. CHART STYLE: Dark theme via plt.style.use('dark_background'). "
                    "Use accent '#00d4aa' for main data series."
                )
            else:
                chart_rule = (
                    "3. DO NOT generate any code using matplotlib, charts, plt, or any visualisation library. "
                    "The user is NOT authorised for charts on their current plan. "
                    "Only return data manipulation code."
                )

            prompt = f"""You are a senior Python Data Analyst. The user has a Pandas DataFrame named 'df'.

DATAFRAME SCHEMA (column · dtype · nulls · value ranges):
{df_summary}

SAMPLE DATA (first 3 rows as JSON):
{current_df.head(3).to_json(orient='records', indent=2)}

USER TASK: {final_query}

STRICT RULES:
1. Return ONLY valid Python code. No markdown, no explanations, no backticks.
2. DATA TASKS: Modify 'df' in place (filter, add columns, sort, etc.).
{chart_rule}
5. Do NOT import libraries — df, plt, pd, and buf are already available.
"""

            last_error   = None
            clean_code   = ""
            exec_success = False

            with st.status("⚡ Nexus Engine Running…", expanded=True) as status:
                for attempt in range(2):
                    try:
                        st.write("📡 Connecting to Gemini…" if attempt == 0 else "🔁 Retrying with error context…")

                        retry_prompt = prompt if attempt == 0 else (
                            prompt + f"\n\nYour previous attempt failed with:\n`{last_error}`\nFix the code."
                        )

                        raw_response = call_gemini_with_timeout(client, retry_prompt)
                        st.write("🧬 Parsing generated code…")
                        clean_code = clean_ai_code(raw_response)

                        if not is_likely_python(clean_code):
                            raise ValueError(
                                "AI returned an explanation instead of code. "
                                f"Preview: {clean_code[:120]}"
                            )

                        buf       = io.BytesIO()
                        local_ctx = {
                            'df':  current_df.copy(),
                            'plt': plt,
                            'pd':  pd,
                            'buf': buf,
                        }

                        plt.style.use('dark_background')
                        st.write("🚀 Executing analysis…")
                        exec(compile(clean_code, "<nexus_ai>", "exec"), {}, local_ctx)

                        result_df = local_ctx.get('df')
                        if isinstance(result_df, pd.DataFrame):
                            st.session_state.updated_df = result_df

                        if CHART_ENABLED and local_ctx['buf'].tell() > 0:
                            local_ctx['buf'].seek(0)
                            st.session_state.chart_gallery.append({
                                "label":     final_query[:60],
                                "img_bytes": local_ctx['buf'].getvalue(),
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                            })

                        exec_success = True
                        break

                    except Exception as e:
                        last_error = str(e)
                        if attempt == 1:
                            status.update(label="❌ Execution Failed", state="error", expanded=True)
                            st.error(f"**Error:** `{last_error}`")
                            st.code(clean_code or "No code generated.", language="python")

            rows_after = (
                len(st.session_state.updated_df)
                if st.session_state.updated_df is not None else rows_before
            )

            st.session_state.command_history.append({
                "cmd":         final_query,
                "ts":          datetime.datetime.now().strftime("%H:%M:%S"),
                "ok":          exec_success,
                "rows_before": rows_before,
                "rows_after":  rows_after,
            })
            st.session_state.request_count += 1
            st.session_state.query_text     = ""
            trim_memory()

            if exec_success:
                row_diff = rows_after - rows_before
                diff_str = (f"+{row_diff:,}" if row_diff >= 0 else f"{row_diff:,}") + " rows"
                status.update(label=f"✅ Done — {diff_str}", state="complete", expanded=False)
                time.sleep(0.4)
                st.rerun()

    # ── Results Panel ──────────────────────────────────────────
    has_chart = bool(st.session_state.chart_gallery) and CHART_ENABLED
    has_table = st.session_state.updated_df is not None

    if has_table or has_chart:
        st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)
        st.markdown('<div class="results-panel">', unsafe_allow_html=True)

        if has_table and has_chart:
            col_table, col_chart = st.columns([1, 1], gap="large")
        elif has_chart:
            col_chart = st.container(); col_table = None
        else:
            col_table = st.container(); col_chart = None

        if col_table and has_table:
            with col_table:
                st.markdown("**Updated Table**")
                st.dataframe(st.session_state.updated_df.head(15), use_container_width=True)

        if col_chart and has_chart:
            with col_chart:
                latest = st.session_state.chart_gallery[-1]
                st.markdown("**Latest Chart**")
                st.image(latest["img_bytes"], use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Chart gallery
        if has_chart and len(st.session_state.chart_gallery) > 1:
            st.markdown('<div class="section-label">Chart Gallery</div>', unsafe_allow_html=True)
            for entry in reversed(st.session_state.chart_gallery[:-1]):
                st.markdown(f'<div class="chart-gallery-item"><div class="chart-gallery-label">◈ {entry["label"]} · {entry["timestamp"]}</div>',
                            unsafe_allow_html=True)
                st.image(entry["img_bytes"], use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # Downloads
        if has_table:
            st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.updated_df.to_excel(writer, index=False)
            dl1, dl2, _ = st.columns([1, 1, 3])
            with dl1:
                st.download_button(
                    "📥 Download Excel",
                    data=output.getvalue(),
                    file_name="nexus_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with dl2:
                st.download_button(
                    "📥 Download CSV",
                    data=st.session_state.updated_df.to_csv(index=False).encode('utf-8'),
                    file_name="nexus_output.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

except Exception as e:
    st.error(f"**Initialization Error:** {e}")
    st.caption("Check your Gemini API Key in the sidebar.")
