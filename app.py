"""
AI Interview Coach — Premium SaaS Shell (Phase 1)
Glassmorphism sidebar · Custom routing · Dark luxury theme
"""
import streamlit as st
import uuid
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import database as db
db.initialize_database()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:16]
    db.upsert_user(st.session_state.session_id)

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"


# ─── CSS: Variables + Global Reset ──────────────────────────────────────────
_CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg-base:      #020617;
  --bg-deep:      #071029;
  --bg-surface:   #0F172A;
  --bg-card:      #0d1b2e;
  --border:       rgba(255,255,255,0.06);
  --border-hi:    rgba(255,255,255,0.10);
  --accent:       #2563EB;
  --accent-mid:   #3B82F6;
  --accent-light: #60A5FA;
  --accent-glow:  rgba(37,99,235,0.30);
  --purple:       #7C3AED;
  --cyan:         #06B6D4;
  --text-1:       #F8FAFC;
  --text-2:       #CBD5E1;
  --text-3:       #64748B;
  --text-4:       #334155;
  --success:      #22C55E;
  --warning:      #F59E0B;
  --danger:       #EF4444;
  --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-xl: 24px;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.4);
  --shadow-md: 0 8px 32px rgba(0,0,0,0.5);
  --shadow-lg: 0 24px 64px rgba(0,0,0,0.6);
  --ease: all 0.25s cubic-bezier(0.4,0,0.2,1);
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--bg-base) !important;
  color: var(--text-1) !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Hide every piece of Streamlit chrome — current + legacy selectors */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebarNav"],
nav[data-testid="stSidebarNav"],
section[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavSeparator"],
.stDeployButton,
.viewerBadge_link__qRIco,
.viewerBadge_container__1QSob { display: none !important; }

.main .block-container {
  padding: 2rem 2.5rem 4rem !important;
  max-width: 1440px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }

/* Page fade-in */
@keyframes page-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.main .block-container { animation: page-in 0.35s ease-out; }
</style>
"""

# ─── CSS: Sidebar ────────────────────────────────────────────────────────────
_CSS_SIDEBAR = """
<style>
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071029 0%, #020617 100%) !important;
  border-right: 1px solid rgba(37,99,235,0.12) !important;
  box-shadow: 4px 0 40px rgba(0,0,0,0.5) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* Kill default button chrome inside sidebar */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--text-3) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  text-align: left !important;
  padding: 0.6rem 0.75rem !important;
  border-radius: var(--r-md) !important;
  width: 100% !important;
  transition: var(--ease) !important;
  letter-spacing: 0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(37,99,235,0.08) !important;
  color: var(--text-2) !important;
  transform: translateX(2px) !important;
}

/* Sidebar logo block */
.sb-logo {
  padding: 1.75rem 1.25rem 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.5rem;
}
.sb-logo-icon {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, #2563EB, #7C3AED);
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
  box-shadow: 0 0 20px rgba(37,99,235,0.35);
  margin-bottom: 0.85rem;
}
.sb-logo-name {
  font-size: 0.95rem; font-weight: 700;
  color: var(--text-1); letter-spacing: -0.02em;
}
.sb-logo-tag {
  font-size: 0.65rem; font-weight: 600;
  color: var(--text-4); text-transform: uppercase; letter-spacing: 0.12em;
  margin-top: 0.1rem;
}

/* Nav section label */
.sb-section {
  font-weight: 700; color: var(--text-4);
  text-transform: uppercase; letter-spacing: 0.14em;
  font-size: 0.62rem;
  padding: 0.75rem 1.25rem 0.4rem;
}

/* Active nav pill */
.sb-nav-active {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  margin: 0 0.25rem;
  border-radius: var(--r-md);
  background: rgba(37,99,235,0.12);
  border: 1px solid rgba(37,99,235,0.2);
  color: var(--accent-light);
  font-size: 0.875rem; font-weight: 600;
  box-shadow: 0 0 20px rgba(37,99,235,0.08);
}
.sb-nav-active-bar {
  width: 3px; height: 18px;
  background: linear-gradient(180deg, #2563EB, #7C3AED);
  border-radius: 2px; flex-shrink: 0;
}

/* Divider */
.sb-hr {
  border: none; border-top: 1px solid var(--border);
  margin: 0.75rem 1.25rem;
}

/* Stats mini */
.sb-stats {
  padding: 0.85rem 1.25rem;
  margin: 0 0.25rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
}
.sb-stats-title {
  font-size: 0.6rem; font-weight: 700;
  color: var(--text-4); text-transform: uppercase; letter-spacing: 0.12em;
  margin-bottom: 0.65rem;
}
.sb-stat-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.35rem;
}
.sb-stat-row:last-child { margin-bottom: 0; }
.sb-stat-lbl { font-size: 0.78rem; color: var(--text-3); }
.sb-stat-val { font-size: 0.78rem; font-weight: 700; color: var(--text-1); }
.sb-stat-val.accent { color: var(--accent-light); }

/* Session badge */
.sb-session {
  font-size: 0.65rem; color: var(--text-4);
  padding: 0.65rem 1.25rem;
  font-family: 'JetBrains Mono', monospace;
}
</style>
"""

# ─── CSS: Buttons + Forms + Widgets ─────────────────────────────────────────
_CSS_WIDGETS = """
<style>
/* Primary button */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB, #1d4ed8) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--r-md) !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  padding: 0.6rem 1.5rem !important;
  font-family: 'Inter', sans-serif !important;
  box-shadow: 0 4px 20px rgba(37,99,235,0.35) !important;
  transition: var(--ease) !important;
  letter-spacing: -0.01em !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
  box-shadow: 0 6px 28px rgba(37,99,235,0.5) !important;
  transform: translateY(-1px) !important;
}

/* Secondary button */
.stButton > button:not([kind="primary"]) {
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-3) !important;
  border: 1px solid var(--border-hi) !important;
  border-radius: var(--r-md) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  padding: 0.6rem 1.5rem !important;
  font-family: 'Inter', sans-serif !important;
  box-shadow: none !important;
  transition: var(--ease) !important;
}
.stButton > button:not([kind="primary"]):hover {
  background: rgba(255,255,255,0.08) !important;
  color: var(--text-2) !important;
  transform: translateY(-1px) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] label { color: var(--text-3) !important; font-size: 0.8rem !important; font-weight: 500 !important; }
[data-testid="stSelectbox"] > div > div > div {
  background: rgba(13,27,46,0.9) !important;
  border: 1px solid var(--border-hi) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-1) !important;
}

/* Slider */
.stSlider label { color: var(--text-3) !important; font-size: 0.8rem !important; font-weight: 500 !important; }

/* Textarea */
[data-testid="stTextArea"] > div > div > textarea {
  background: rgba(7,16,41,0.95) !important;
  border: 1px solid var(--border-hi) !important;
  border-radius: var(--r-lg) !important;
  color: var(--text-1) !important;
  font-size: 0.9rem !important;
  font-family: 'Inter', sans-serif !important;
  padding: 1rem !important;
  transition: border-color 0.2s !important;
  resize: vertical !important;
}
[data-testid="stTextArea"] > div > div > textarea:focus {
  border-color: rgba(37,99,235,0.5) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
  outline: none !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: rgba(7,16,41,0.8) !important;
  border: 2px dashed rgba(255,255,255,0.08) !important;
  border-radius: var(--r-lg) !important;
}

/* Progress bar */
.stProgress > div > div { background: rgba(255,255,255,0.05) !important; border-radius: 100px !important; height: 5px !important; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #2563EB, #7C3AED) !important; border-radius: 100px !important; }

/* Expander */
[data-testid="stExpander"] {
  background: rgba(13,27,46,0.8) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"] summary { color: var(--text-2) !important; font-size: 0.875rem !important; font-weight: 500 !important; }

/* Alerts */
[data-testid="stAlert"] { border-radius: var(--r-md) !important; font-size: 0.875rem !important; }
</style>
"""

# ─── CSS: Shared Components (cards, table, tags, badges) ────────────────────
_CSS_COMPONENTS = """
<style>
/* Glass card */
.glass-card {
  background: linear-gradient(135deg, rgba(13,27,46,0.92), rgba(7,16,41,0.96));
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 1.75rem;
  position: relative; overflow: hidden;
  -webkit-backdrop-filter: blur(20px); /* Safari fallback */
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-md), inset 0 1px 0 rgba(255,255,255,0.04);
  transition: var(--ease);
}
.glass-card:hover {
  border-color: rgba(37,99,235,0.2);
  box-shadow: var(--shadow-lg), 0 0 40px rgba(37,99,235,0.12);
  transform: translateY(-2px);
}
.glass-card::before {
  content:''; position:absolute; top:0;left:0;right:0; height:1px;
  background: linear-gradient(90deg, transparent, rgba(37,99,235,0.35), transparent);
}

/* Generic card */
.card {
  background: rgba(13,27,46,0.85);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.25rem 1.5rem;
  margin-bottom: 0.75rem;
}

/* KPI card */
.kpi-card {
  background: linear-gradient(135deg, rgba(13,27,46,0.95), rgba(7,16,41,0.98));
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 1.5rem 1.25rem;
  position: relative; overflow: hidden;
  transition: var(--ease);
  box-shadow: var(--shadow-sm);
  cursor: default;
}
.kpi-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255,255,255,0.1);
  box-shadow: var(--shadow-md), 0 0 30px var(--kpi-glow, rgba(37,99,235,0.12));
}
.kpi-card::after {
  content:''; position:absolute; bottom:0;left:0;right:0; height:2px;
  background: var(--kpi-accent, #2563EB); opacity:0; transition:opacity 0.3s;
}
.kpi-card:hover::after { opacity: 1; }
.kpi-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem; }
.kpi-icon {
  width:40px; height:40px; border-radius:var(--r-sm);
  display:flex; align-items:center; justify-content:center; font-size:1.1rem;
  background: var(--kpi-icon-bg, rgba(37,99,235,0.12));
  border: 1px solid var(--kpi-icon-border, rgba(37,99,235,0.2));
}
.kpi-value { font-size:2rem; font-weight:900; color:var(--text-1); letter-spacing:-0.04em; line-height:1; margin-bottom:0.25rem; }
.kpi-label { font-size:0.72rem; color:var(--text-3); font-weight:600; text-transform:uppercase; letter-spacing:0.08em; }

/* Chart wrapper */
.chart-wrap {
  background: linear-gradient(135deg, rgba(13,27,46,0.9), rgba(7,16,41,0.95));
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: var(--shadow-sm);
  position: relative; overflow: hidden;
}
.chart-wrap::before {
  content:''; position:absolute; top:0;left:0;right:0; height:1px;
  background: linear-gradient(90deg, transparent, rgba(37,99,235,0.25), transparent);
}
.chart-title { font-size:0.85rem; font-weight:600; color:var(--text-2); margin-bottom:0.2rem; }
.chart-sub   { font-size:0.7rem;  color:var(--text-3); margin-bottom:0.9rem; }

/* Data table */
.data-table {
  background: rgba(13,27,46,0.8); border:1px solid var(--border);
  border-radius: var(--r-xl); overflow:hidden; box-shadow: var(--shadow-sm);
}
.t-head { display:grid; padding:0.7rem 1.5rem; background:rgba(255,255,255,0.02); border-bottom:1px solid var(--border); }
.t-row  { display:grid; padding:0.8rem 1.5rem; border-bottom:1px solid rgba(255,255,255,0.025); transition:background 0.2s; }
.t-row:hover { background:rgba(37,99,235,0.04); }
.t-row:last-child { border-bottom:none; }
.th { font-size:0.65rem; font-weight:700; color:var(--text-4); text-transform:uppercase; letter-spacing:0.1em; }
.td { font-size:0.85rem; color:var(--text-2); display:flex; align-items:center; }
.td.bold  { font-weight:700; color:var(--text-1); }
.td.muted { color:var(--text-3); font-size:0.78rem; }

/* Topic pills / tags */
.topic-pill {
  display:inline-block; background:rgba(37,99,235,0.1);
  border:1px solid rgba(37,99,235,0.2); color:var(--accent-light);
  border-radius:100px; padding:0.25rem 0.85rem;
  font-size:0.75rem; font-weight:500; margin:0.2rem 0.15rem;
  transition:var(--ease);
}
.topic-pill:hover { background:rgba(37,99,235,0.18); }

/* List items */
.list-item { display:flex; align-items:flex-start; gap:0.6rem; padding:0.4rem 0; font-size:0.875rem; line-height:1.55; border-bottom:1px solid rgba(255,255,255,0.025); }
.list-item:last-child { border-bottom:none; }
.li-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; margin-top:0.45rem; }
.list-item.positive { color:var(--text-2); }
.list-item.positive .li-dot { background:var(--success); }
.list-item.negative { color:var(--text-3); }
.list-item.negative .li-dot { background:var(--warning); }

/* Page titles */
.page-title {
  font-size:1.85rem; font-weight:800; letter-spacing:-0.04em;
  background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.page-sub { font-size:0.9rem; color:var(--text-3); margin-top:0.3rem; }

/* Insight card — used in interview.py completion + reports.py */
.insight-card {
  background: rgba(13,27,46,0.85);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.1rem 1.25rem;
  margin-bottom: 0.6rem;
  transition: var(--ease);
}
.insight-card:hover {
  border-color: rgba(255,255,255,0.09);
  box-shadow: var(--shadow-sm);
}

/* Summary block — paragraph inside insight-card */
.summary-block {
  font-size: 0.875rem;
  color: var(--text-3);
  line-height: 1.8;
}

/* Section eyebrow — small uppercase label above sections */
/* Shared token with .sb-section: same weight/color/case/tracking; differs only in size + spacing */
.section-eyebrow, .sb-section {
  font-weight: 700; color: var(--text-4);
  text-transform: uppercase; letter-spacing: 0.14em;
}
.section-eyebrow {
  font-size: 0.7rem;
  margin-bottom: 0.65rem;
}

/* Loading skeleton */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(90deg,
    rgba(255,255,255,0.04) 25%,
    rgba(255,255,255,0.07) 50%,
    rgba(255,255,255,0.04) 75%);
  background-size: 800px 100%;
  animation: shimmer 1.6s infinite linear;
  border-radius: var(--r-sm);
}
.skeleton-card {
  background: rgba(13,27,46,0.8);
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 1.5rem;
  overflow: hidden;
}
.skeleton-line { height: 12px; margin-bottom: 10px; }
.skeleton-line.w-60  { width: 60%; }
.skeleton-line.w-80  { width: 80%; }
.skeleton-line.w-40  { width: 40%; }
.skeleton-line.w-100 { width: 100%; }

/* Empty state — used by all three pages */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 5rem 2rem;
}
.empty-state-icon {
  width: 72px; height: 72px; border-radius: 50%;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, rgba(37,99,235,0.12), rgba(124,58,237,0.12));
  border: 1px solid rgba(37,99,235,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem;
  box-shadow: 0 0 40px rgba(37,99,235,0.08);
}
.empty-state-title {
  font-size: 1.4rem; font-weight: 800; color: var(--text-1);
  letter-spacing: -0.03em; margin-bottom: 0.6rem;
}
.empty-state-sub {
  font-size: 0.9rem; color: var(--text-3);
  max-width: 380px; margin: 0 auto 2rem; line-height: 1.65;
}
</style>
"""

# ─── CSS: Interview Page ─────────────────────────────────────────────────────
_CSS_INTERVIEW = """
<style>
.question-panel {
  background: linear-gradient(135deg, rgba(13,27,46,0.95), rgba(7,16,41,0.98));
  border: 1px solid rgba(37,99,235,0.2);
  border-radius: var(--r-xl);
  padding: 2rem 2.25rem;
  position: relative; overflow: hidden;
  box-shadow: var(--shadow-md), inset 0 1px 0 rgba(255,255,255,0.04);
  margin-bottom: 1.25rem;
}
.question-panel::before {
  content:''; position:absolute; top:0;left:0;right:0; height:3px;
  background: linear-gradient(90deg, #2563EB, #7C3AED, #06B6D4);
}
.question-panel::after {
  content:''; position:absolute; top:-80px; right:-80px;
  width:200px; height:200px;
  background: radial-gradient(circle, rgba(37,99,235,0.07) 0%, transparent 70%);
  pointer-events:none;
}
.q-eyebrow { font-size:0.65rem; font-weight:700; color:var(--accent-light); text-transform:uppercase; letter-spacing:0.18em; margin-bottom:0.9rem; }
.q-text    { font-size:1.05rem; color:var(--text-1); line-height:1.75; font-weight:400; }

/* AI panel */
.ai-panel {
  background: linear-gradient(180deg, rgba(13,27,46,0.98), rgba(7,16,41,1));
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 1.75rem 1.5rem;
  box-shadow: var(--shadow-md);
  text-align: center;
}
.ai-avatar {
  width:68px; height:68px; border-radius:50%;
  background: linear-gradient(135deg, #2563EB, #7C3AED);
  display:flex; align-items:center; justify-content:center;
  font-size:1.65rem; margin: 0 auto 1rem;
  box-shadow: 0 0 28px rgba(37,99,235,0.4), 0 0 56px rgba(124,58,237,0.2);
  animation: avatar-pulse 2.5s ease-in-out infinite;
  position:relative;
}
.ai-avatar::after {
  content:''; position:absolute; inset:-5px; border-radius:50%;
  border:1px solid rgba(37,99,235,0.25);
  animation: avatar-ring 2.5s ease-in-out infinite;
}
@keyframes avatar-pulse {
  0%,100% { box-shadow:0 0 28px rgba(37,99,235,0.4),0 0 56px rgba(124,58,237,0.2); }
  50%      { box-shadow:0 0 44px rgba(37,99,235,0.6),0 0 72px rgba(124,58,237,0.3); }
}
@keyframes avatar-ring {
  0%,100% { transform:scale(1); opacity:.5; }
  50%      { transform:scale(1.1); opacity:.15; }
}
.ai-name   { font-size:0.875rem; font-weight:700; color:var(--text-1); }
.ai-role   { font-size:0.68rem; color:var(--text-3); margin:0.15rem 0 1rem; }
.ai-online { display:inline-flex; align-items:center; gap:0.4rem; font-size:0.7rem; color:var(--success); }
.ai-dot    { width:6px; height:6px; background:var(--success); border-radius:50%; animation:dot-blink 1.5s ease infinite; }
@keyframes dot-blink { 0%,100%{opacity:1} 50%{opacity:0.25} }

/* Score panel */
.score-panel {
  background:rgba(13,27,46,0.9); border:1px solid var(--border);
  border-radius:var(--r-xl); padding:1.5rem; box-shadow:var(--shadow-sm);
}
.score-big { font-size:2.75rem; font-weight:900; text-align:center; letter-spacing:-0.05em; line-height:1; }
.score-big-lbl { text-align:center; font-size:0.65rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.12em; margin:.2rem 0 1.1rem; }
.sb-row { display:flex; align-items:center; gap:0.55rem; margin-bottom:0.55rem; }
.sb-lbl { font-size:0.68rem; color:var(--text-3); width:3.3rem; flex-shrink:0; }
.sb-track { flex:1; height:4px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden; }
.sb-fill  { height:100%; border-radius:2px; transition:width 0.7s cubic-bezier(0.4,0,0.2,1); }
.sb-val   { font-size:0.72rem; font-weight:700; width:1.3rem; text-align:right; }

/* Feedback bubble */
.fb-bubble {
  background:rgba(37,99,235,0.06); border:1px solid rgba(37,99,235,0.14);
  border-left:3px solid var(--accent);
  border-radius:0 var(--r-md) var(--r-md) 0;
  padding:0.9rem 1.2rem; margin-bottom:1.2rem;
}
.fb-score { font-size:0.78rem; font-weight:700; margin-bottom:0.3rem; }
.fb-text  { font-size:0.875rem; color:var(--text-3); line-height:1.65; }
</style>
"""

# ─── CSS: Report + Completion Pages ─────────────────────────────────────────
_CSS_REPORTS = """
<style>
/* Completion hero */
.result-hero {
  text-align:center; padding:3rem 2rem 2.5rem;
  background: linear-gradient(135deg, rgba(13,27,46,0.95), rgba(7,16,41,0.98));
  border:1px solid var(--border); border-radius:var(--r-xl);
  margin-bottom:2rem; position:relative; overflow:hidden;
  box-shadow:var(--shadow-lg);
}
.result-hero::before {
  content:''; position:absolute; inset:0;
  background: radial-gradient(ellipse at 50% 0%, rgba(37,99,235,0.1) 0%, transparent 60%);
  pointer-events:none;
}
.rh-icon  { font-size:3rem; display:block; margin-bottom:0.9rem; }
.rh-score { font-size:4.5rem; font-weight:900; letter-spacing:-0.05em; line-height:1; }
.rh-lbl   { font-size:0.82rem; color:var(--text-3); margin:0.5rem 0 1.2rem; }
.rh-badge { display:inline-block; padding:0.45rem 1.4rem; border-radius:100px; font-size:0.85rem; font-weight:700; border:1px solid; letter-spacing:0.01em; }

.score-card { background:rgba(13,27,46,0.9); border:1px solid var(--border); border-radius:var(--r-lg); padding:1.25rem; text-align:center; transition:var(--ease); }
.score-card:hover { transform:translateY(-2px); border-color:rgba(255,255,255,0.1); }
.sc-num { font-size:1.9rem; font-weight:800; letter-spacing:-0.04em; }
.sc-lbl { font-size:0.68rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; margin-top:0.25rem; }

/* Report page header */
.report-hdr {
  background: linear-gradient(135deg, rgba(13,27,46,0.95), rgba(7,16,41,0.98));
  border:1px solid var(--border); border-radius:var(--r-xl);
  padding:2rem 2.25rem; display:flex; justify-content:space-between; align-items:center;
  box-shadow:var(--shadow-md); position:relative; overflow:hidden;
}
.report-hdr::before { content:''; position:absolute; top:0;left:0;right:0; height:2px; background:linear-gradient(90deg,#2563EB,#7C3AED,#06B6D4); }
.rh2-role  { font-size:1.4rem; font-weight:800; color:var(--text-1); letter-spacing:-0.03em; }
.rh2-meta  { font-size:0.8rem; color:var(--text-3); margin:.3rem 0 .7rem; }
.rh2-badge { display:inline-block; padding:.3rem .95rem; border-radius:100px; font-size:.75rem; font-weight:700; border:1px solid; }
.rh2-score { font-size:3.75rem; font-weight:900; letter-spacing:-0.05em; line-height:1; }
.rh2-denom { font-size:1rem; color:var(--text-3); }

/* Q&A detail */
.qa-q   { font-size:.875rem; color:var(--text-3); line-height:1.65; margin-bottom:.7rem; }
.qa-a   { background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--r-sm); padding:.85rem 1rem; font-size:.875rem; color:var(--text-2); line-height:1.7; }
.qa-fb  { background:rgba(37,99,235,0.06); border-left:3px solid var(--accent); padding:.8rem 1rem; border-radius:0 var(--r-sm) var(--r-sm) 0; font-size:.875rem; color:var(--text-3); line-height:1.65; }
.mr-row { display:flex; align-items:center; gap:.5rem; margin-bottom:.55rem; }
.mr-lbl { font-size:.68rem; color:var(--text-3); width:5.5rem; flex-shrink:0; }
.mr-track { flex:1; height:4px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden; }
.mr-fill  { height:100%; border-radius:2px; }
.mr-val   { font-size:.72rem; font-weight:700; width:1.3rem; text-align:right; }
</style>
"""


# ─── inject_css() ────────────────────────────────────────────────────────────
def inject_css():
    """
    Emit all CSS in a single <style> tag and only once per session.

    Six separate st.markdown() calls previously added a new set of <style>
    tags on every Streamlit rerun, causing progressive DOM bloat and potential
    style flicker. This version:
      - Strips the individual <style>/<style> wrappers from each block
      - Concatenates the raw CSS into one string
      - Wraps it in a single <style> tag
      - Guards with session_state so the tag is injected exactly once
    """
    if st.session_state.get("_css_injected"):
        return

    # Strip the <style> / </style> wrapper that each block carries,
    # then join all raw CSS into one payload.
    blocks = (
        _CSS_BASE, _CSS_SIDEBAR, _CSS_WIDGETS,
        _CSS_COMPONENTS, _CSS_INTERVIEW, _CSS_REPORTS,
    )
    raw_parts = []
    for block in blocks:
        css = block.strip()
        if css.startswith("<style>"):
            css = css[len("<style>"):]
        if css.endswith("</style>"):
            css = css[: -len("</style>")]
        raw_parts.append(css.strip())

    combined = "\n\n".join(raw_parts)
    st.markdown(f"<style>\n{combined}\n</style>", unsafe_allow_html=True)
    st.session_state["_css_injected"] = True


# ─── _get_cached_stats() ─────────────────────────────────────────────────────
def _get_cached_stats(session_id: str) -> dict:
    """
    Return dashboard stats from session_state cache.

    The cache is populated on first call and invalidated whenever
    st.session_state._stats_dirty is True (set by any page that
    completes an interview).  This prevents a DB round-trip on
    every Streamlit rerun while keeping the sidebar figures fresh.
    """
    cache_key = f"_sidebar_stats_{session_id}"

    # Honour an explicit invalidation request from other pages.
    if st.session_state.pop("_stats_dirty", False):
        st.session_state.pop(cache_key, None)

    if cache_key not in st.session_state:
        st.session_state[cache_key] = db.get_dashboard_stats(session_id)
        logger.debug("sidebar stats cache populated for session %s", session_id)
    else:
        logger.debug("sidebar stats served from cache for session %s", session_id)

    return st.session_state[cache_key]


# ─── render_sidebar() ────────────────────────────────────────────────────────
def render_sidebar():
    session_id = st.session_state.session_id
    stats      = _get_cached_stats(session_id)
    total      = stats.get("total_interviews", 0)
    avg        = stats.get("avg_score") or 0.0
    active     = st.session_state.active_page

    with st.sidebar:
        # Logo
        st.markdown(
            """
            <div class="sb-logo">
              <div class="sb-logo-icon">🎯</div>
              <div class="sb-logo-name">Interview Coach</div>
              <div class="sb-logo-tag">Powered by Llama 3.3 · 70B</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Nav
        st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)

        nav_items = [
            ("Dashboard",        "🏠", "Dashboard"),
            ("Interview",        "🎤", "Interview"),
            ("Resume Analyzer",  "📄", "Resume Analyzer"),
            ("Reports",          "📋", "Reports"),
            ("Settings",         "⚙️", "Settings"),
        ]

        for page, icon, label in nav_items:
            if active == page:
                # Render active state as static HTML (no interaction needed)
                st.markdown(
                    f'<div class="sb-nav-active">'
                    f'<div class="sb-nav-active-bar"></div>'
                    f'<span>{icon}&nbsp;&nbsp;{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{page}",
                             use_container_width=True):
                    st.session_state.active_page = page
                    st.rerun()

        # Divider
        st.markdown('<hr class="sb-hr">', unsafe_allow_html=True)

        # Stats mini-card
        st.markdown(
            f"""
            <div class="sb-stats">
              <div class="sb-stats-title">Your Progress</div>
              <div class="sb-stat-row">
                <span class="sb-stat-lbl">Interviews</span>
                <span class="sb-stat-val">{total}</span>
              </div>
              <div class="sb-stat-row">
                <span class="sb-stat-lbl">Avg Score</span>
                <span class="sb-stat-val accent">{avg}/10</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Session badge
        st.markdown(
            f'<div class="sb-session">Session&nbsp;·&nbsp;{session_id[:12]}…</div>',
            unsafe_allow_html=True,
        )


# ─── API warning banner ───────────────────────────────────────────────────────
def _render_api_warning():
    from services.ai_service import is_api_available
    if not is_api_available():
        st.warning(
            "**GROQ_API_KEY not configured.** "
            "AI features are disabled. "
            "Add `GROQ_API_KEY=gsk_...` to your `.env` file and restart. "
            "Get a free key at [console.groq.com](https://console.groq.com).",
            icon="🔑",
        )


# ─── main() ──────────────────────────────────────────────────────────────────
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
    elif page == "Resume Analyzer":
        from pages.resume_analyzer import render
        render()
    elif page == "Reports":
        from pages.reports import render
        render()
    elif page == "Settings":
        from pages.settings import render
        render()
    else:
        from pages.dashboard import render
        render()


if __name__ == "__main__":
    main()
