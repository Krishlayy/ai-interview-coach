"""
AI Interview Coach — Main Application Entry Point
Production-grade Streamlit application.
"""

import streamlit as st
import uuid
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Page Config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Database Init — singleton-guarded, runs once per process ─────────────────
from database import database as db
db.initialize_database()          # safe to call multiple times; no-op after first run

# ─── Session Bootstrap ─────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:16]
    db.upsert_user(st.session_state.session_id)

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"

# ─── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
/* ─── Reset & Base ─────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0f1e !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: #0a0f1e !important;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
.stDeployButton { display: none; }

/* ─── Sidebar ──────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1424 !important;
    border-right: 1px solid rgba(59,130,246,0.15) !important;
    padding-top: 0 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}

.sidebar-logo {
    text-align: center;
    padding: 1.5rem 1rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1rem;
}

.sidebar-logo-icon {
    font-size: 2.5rem;
    display: block;
    margin-bottom: 0.4rem;
}

.sidebar-logo-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: -0.02em;
}

.sidebar-logo-sub {
    font-size: 0.72rem;
    color: #4b5563;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 1.2rem;
    margin: 0.15rem 0.5rem;
    border-radius: 10px;
    cursor: pointer;
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s ease;
    text-decoration: none;
}

.nav-item:hover {
    background: rgba(59,130,246,0.08);
    color: #e2e8f0;
}

.nav-item.active {
    background: rgba(59,130,246,0.15);
    color: #60a5fa;
    border-left: 3px solid #3b82f6;
}

.nav-icon { font-size: 1.1rem; width: 1.3rem; }

.sidebar-section-label {
    font-size: 0.65rem;
    font-weight: 600;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 0.5rem 1.7rem 0.2rem;
    margin-top: 0.5rem;
}

.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 0.75rem 1rem;
}

.session-badge {
    font-size: 0.72rem;
    color: #4b5563;
    padding: 0.5rem 1.2rem;
    word-break: break-all;
}

/* ─── Main Content ─────────────────────────────────────────────────────── */
.main .block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1400px !important;
}

.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #f1f5f9;
    margin-bottom: 0.25rem;
    letter-spacing: -0.03em;
}

.subtitle {
    color: #64748b;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* ─── Cards ────────────────────────────────────────────────────────────── */
.card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
}

.kpi-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}

.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(59,130,246,0.3);
}

.kpi-icon { font-size: 1.6rem; margin-bottom: 0.5rem; }
.kpi-value { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.03em; }
.kpi-label { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }

.chart-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

.chart-card h4, .chart-card #### {
    font-size: 0.9rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 0.75rem;
}

/* ─── Interview Setup ──────────────────────────────────────────────────── */
.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.stat-label { color: #64748b; font-size: 0.85rem; }
.stat-value { color: #e2e8f0; font-size: 0.9rem; font-weight: 600; }

.tips-list {
    color: #64748b;
    font-size: 0.82rem;
    padding-left: 1.2rem;
    line-height: 1.9;
}

/* ─── Active Interview ─────────────────────────────────────────────────── */
.question-counter {
    text-align: right;
    color: #64748b;
    font-size: 0.85rem;
    font-weight: 600;
    padding-top: 6px;
}

.question-card {
    background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
}

.question-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.question-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #3b82f6;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.75rem;
}

.question-text {
    font-size: 1.05rem;
    color: #f1f5f9;
    line-height: 1.7;
    font-weight: 400;
}

.answer-container { margin-top: 0.5rem; }

[data-testid="stTextArea"] > div > div > textarea {
    background: #0d1424 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    padding: 1rem !important;
    font-family: 'Inter', sans-serif !important;
    resize: vertical !important;
    transition: border-color 0.2s !important;
}

[data-testid="stTextArea"] > div > div > textarea:focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
    outline: none !important;
}

.feedback-card {
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}

.feedback-score {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
}

.feedback-text {
    color: #94a3b8;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ─── Live Scores Widget ───────────────────────────────────────────────── */
.live-scores {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.25rem 1rem;
}

.live-scores-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 1rem;
}

.no-scores {
    color: #374151;
    font-size: 0.85rem;
    text-align: center;
    padding: 1rem 0;
}

.live-overall {
    font-size: 2.4rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 1rem;
    letter-spacing: -0.04em;
}

.live-denom {
    font-size: 1.1rem;
    color: #374151;
    font-weight: 400;
}

.score-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.6rem;
}

.score-row-label {
    font-size: 0.75rem;
    color: #64748b;
    width: 3.5rem;
    flex-shrink: 0;
}

.score-bar-bg {
    flex: 1;
    height: 5px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

.score-row-val {
    font-size: 0.78rem;
    font-weight: 600;
    width: 1.5rem;
    text-align: right;
    flex-shrink: 0;
}

/* ─── Report / Completion ──────────────────────────────────────────────── */
.report-hero {
    text-align: center;
    padding: 2.5rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2rem;
}

.report-icon { font-size: 3rem; margin-bottom: 0.75rem; }
.report-score { font-size: 3.5rem; font-weight: 900; letter-spacing: -0.04em; }
.report-title { font-size: 1rem; color: #64748b; margin: 0.25rem 0 1rem; font-weight: 500; }
.report-rec {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    border-radius: 100px;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.score-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.2rem 0.75rem;
    text-align: center;
}

.score-num { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.03em; }
.score-lbl { font-size: 0.72rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.06em; }

.list-item {
    padding: 0.45rem 0.5rem;
    font-size: 0.88rem;
    border-radius: 6px;
    margin-bottom: 0.3rem;
    line-height: 1.5;
}

.list-item.positive { color: #34d399; background: rgba(52,211,153,0.06); }
.list-item.negative { color: #94a3b8; background: rgba(148,163,184,0.05); }
.list-item.small { font-size: 0.8rem; padding: 0.3rem 0.4rem; }

.tag {
    display: inline-block;
    background: rgba(59,130,246,0.12);
    color: #60a5fa;
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 100px;
    padding: 0.25rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 0.2rem 0.15rem;
}

.summary-text {
    color: #94a3b8;
    font-size: 0.9rem;
    line-height: 1.75;
}

/* ─── Reports Page ─────────────────────────────────────────────────────── */
.report-header-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rh-left {}
.rh-role { font-size: 1.3rem; font-weight: 700; color: #f1f5f9; }
.rh-meta { color: #64748b; font-size: 0.85rem; margin: 0.25rem 0 0.75rem; }
.rh-rec {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid;
}
.rh-right { text-align: right; }
.rh-score { font-size: 3.5rem; font-weight: 900; letter-spacing: -0.04em; line-height: 1; }
.rh-score-label { color: #475569; font-size: 1rem; }

.score-breakdown { margin-bottom: 0.5rem; }
.breakdown-item { text-align: center; }
.breakdown-score { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0.4rem; }
.breakdown-bar-bg {
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
    margin: 0.4rem auto;
    width: 80%;
}
.breakdown-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.breakdown-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.07em; }

.question-text-sm { color: #94a3b8; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.75rem; }
.answer-text { color: #cbd5e1; font-size: 0.88rem; line-height: 1.65; background: rgba(255,255,255,0.02); border-radius: 8px; padding: 0.75rem; }
.feedback-box { background: rgba(59,130,246,0.07); border-left: 3px solid #3b82f6; padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; color: #94a3b8; font-size: 0.88rem; line-height: 1.6; }

.mini-score-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}
.mini-label { font-size: 0.72rem; color: #64748b; width: 5.5rem; flex-shrink: 0; }
.mini-bar-bg { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.mini-bar-fill { height: 100%; border-radius: 2px; }
.mini-val { font-size: 0.75rem; font-weight: 600; width: 1.5rem; text-align: right; }

/* ─── Table ────────────────────────────────────────────────────────────── */
.table-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1rem 1.5rem;
}

.table-header {
    font-size: 0.72rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 0.5rem;
}

.table-cell {
    font-size: 0.88rem;
    color: #cbd5e1;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}

.table-cell.muted { color: #475569; }

/* ─── Empty State ──────────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
}

.empty-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.empty-title { font-size: 1.4rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.5rem; }
.empty-subtitle { color: #64748b; font-size: 0.95rem; max-width: 400px; margin: 0 auto 2rem; }

/* ─── Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.2s ease !important;
    font-family: 'Inter', sans-serif !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(37,99,235,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,0.05) !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

.stButton > button:not([kind="primary"]):hover {
    background: rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
}

/* ─── Form Widgets ─────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stSlider"] > div,
.stSelectSlider > div {
    background: #0d1424 !important;
}

[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
.stSlider label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

[data-testid="stSelectbox"] > div > div > div {
    background: #0d1424 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

[data-testid="stFileUploader"] {
    background: #0d1424 !important;
    border: 2px dashed rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

/* ─── Progress Bar ─────────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
    border-radius: 100px !important;
}

.stProgress > div > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 100px !important;
    height: 6px !important;
}

/* ─── Expander ─────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stExpander"] summary {
    color: #cbd5e1 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* ─── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ─── Spinner ──────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] { color: #3b82f6 !important; }

/* ─── Alerts ───────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Sidebar Navigation ───────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span class="sidebar-logo-icon">🎯</span>
            <div class="sidebar-logo-title">AI Interview Coach</div>
            <div class="sidebar-logo-sub">Powered by Llama 3.3</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)

        nav_items = [
            ("Dashboard", "📊", "Dashboard"),
            ("Interview", "🎤", "Interview"),
            ("Reports", "📋", "Reports"),
        ]

        for page, icon, label in nav_items:
            active_class = "active" if st.session_state.active_page == page else ""
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page}",
                use_container_width=True,
            ):
                st.session_state.active_page = page
                st.rerun()

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # Stats mini
        session_id = st.session_state.session_id
        stats = db.get_dashboard_stats(session_id)
        total = stats.get("total_interviews", 0)
        avg = stats.get("avg_score") or 0

        st.markdown(
            f"""
            <div style="padding: 0.75rem 1.2rem;">
                <div style="font-size:0.65rem;color:#374151;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.6rem;">Your Stats</div>
                <div style="display:flex;justify-content:space-between;margin-bottom:0.35rem;">
                    <span style="font-size:0.8rem;color:#64748b;">Interviews</span>
                    <span style="font-size:0.8rem;font-weight:600;color:#e2e8f0;">{total}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.8rem;color:#64748b;">Avg Score</span>
                    <span style="font-size:0.8rem;font-weight:600;color:#3b82f6;">{avg}/10</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="session-badge">Session: {session_id[:8]}...</div>',
            unsafe_allow_html=True,
        )


# ─── API Key Warning Banner ────────────────────────────────────────────────────
def _render_api_warning():
    """Show a dismissible warning when GROQ_API_KEY is absent."""
    from services.ai_service import is_api_available
    if not is_api_available():
        st.warning(
            "⚠️  **GROQ_API_KEY not configured.** "
            "AI features (question generation, answer evaluation) are disabled. "
            "Add `GROQ_API_KEY=gsk_...` to your `.env` file and restart the app. "
            "Get a free key at [console.groq.com](https://console.groq.com).",
            icon="🔑",
        )


# ─── Main Render Loop ─────────────────────────────────────────────────────────
def main():
    inject_css()
    render_sidebar()
    _render_api_warning()

    page = st.session_state.active_page

    if page == "Dashboard":
        from pages.dashboard import render
        render()
    elif page == "Interview":
        from pages.interview import render
        render()
    elif page == "Reports":
        from pages.reports import render
        render()
    else:
        from pages.dashboard import render
        render()


if __name__ == "__main__":
    main()
