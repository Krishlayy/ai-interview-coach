"""
Dashboard Page — Premium SaaS redesign (Phase 2)
Hero section · KPI cards · Analytics charts · Recent interviews table
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from database import database as db


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def render():
    # Scoped hover upgrade for chart wrappers on this page
    st.markdown(
        """
        <style>
        .chart-wrap { transition: border-color 0.25s, box-shadow 0.25s; }
        .chart-wrap:hover {
            border-color: rgba(37,99,235,0.18);
            box-shadow: 0 8px 40px rgba(0,0,0,0.45), 0 0 30px rgba(37,99,235,0.06);
        }
        @media (max-width: 768px) {
            .kpi-card { padding: 1rem 0.85rem; }
            .kpi-value { font-size: 1.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    session_id = st.session_state.get("session_id", "default")
    stats      = db.get_dashboard_stats(session_id)
    analytics  = db.get_analytics(session_id)

    _render_hero(stats, bool(analytics))

    if not analytics:
        _render_empty_state()
        return

    # CTA row below hero when there IS data
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
    cta1, cta2, cta3 = st.columns([1, 1, 4])
    with cta1:
        if st.button("🎤  New Interview", type="primary", use_container_width=True):
            st.session_state.active_page = "Interview"
            st.rerun()
    with cta2:
        if st.button("📄  Analyze Resume", use_container_width=True):
            st.session_state.active_page = "Resume Analyzer"
            st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _render_kpi_cards(stats)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    df = _build_dataframe(analytics)

    col_l, col_r = st.columns(2, gap="medium")
    with col_l:
        _render_trend_chart(df)
    with col_r:
        _render_skill_radar(df)

    col_l2, col_r2 = st.columns(2, gap="medium")
    with col_l2:
        _render_score_distribution(df)
    with col_r2:
        _render_role_breakdown(df)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _render_recent_interviews(session_id)


# ─────────────────────────────────────────────────────────────────────────────
#  Hero section
# ─────────────────────────────────────────────────────────────────────────────
def _render_hero(stats: dict, has_data: bool):
    total = stats.get("total_interviews", 0)
    avg   = stats.get("avg_score") or 0.0

    if has_data:
        status_html = (
            f'<div class="hero-status">'
            f'<span class="hero-status-dot"></span>'
            f'<span>{total} session{"s" if total != 1 else ""} completed</span>'
            f'<span class="hero-status-sep">·</span>'
            f'<span>Avg score <strong style="color:#60A5FA">{avg}/10</strong></span>'
            f'</div>'
        )
    else:
        status_html = (
            '<div class="hero-status">'
            '<span class="hero-status-dot"></span>'
            '<span>Ready — start your first session below</span>'
            '</div>'
        )

    st.markdown(
        f"""
        <style>
        /* ── Hero ─────────────────────────────────────────────── */
        @keyframes hero-orb-1 {{
            0%,100% {{ transform: translate(0,0) scale(1); opacity:.18; }}
            50%      {{ transform: translate(30px,-20px) scale(1.12); opacity:.28; }}
        }}
        @keyframes hero-orb-2 {{
            0%,100% {{ transform: translate(0,0) scale(1); opacity:.12; }}
            50%      {{ transform: translate(-20px,25px) scale(1.08); opacity:.2; }}
        }}
        @keyframes hero-particle {{
            0%   {{ transform: translateY(0) translateX(0); opacity:0; }}
            10%  {{ opacity:.6; }}
            90%  {{ opacity:.4; }}
            100% {{ transform: translateY(-120px) translateX(20px); opacity:0; }}
        }}
        @keyframes hero-line-in {{
            from {{ transform: scaleX(0); }}
            to   {{ transform: scaleX(1); }}
        }}
        @keyframes hero-fade-up {{
            from {{ opacity:0; transform:translateY(16px); }}
            to   {{ opacity:1; transform:translateY(0); }}
        }}
        @keyframes hero-glow-pulse {{
            0%,100% {{ box-shadow: 0 0 40px rgba(37,99,235,0.25); }}
            50%      {{ box-shadow: 0 0 70px rgba(37,99,235,0.45); }}
        }}
        @keyframes stat-in {{
            from {{ opacity:0; transform:translateY(10px); }}
            to   {{ opacity:1; transform:translateY(0); }}
        }}
        .landing-hero {{
            position: relative;
            padding: 3.5rem 3rem 3rem;
            border-radius: 28px;
            border: 1px solid rgba(255,255,255,0.07);
            background: linear-gradient(
                135deg,
                rgba(7,16,41,0.97) 0%,
                rgba(13,27,56,0.95) 45%,
                rgba(37,16,80,0.55) 100%
            );
            overflow: hidden;
            margin-bottom: 0;
            box-shadow: 0 12px 60px rgba(0,0,0,0.55);
        }}
        /* Accent border top */
        .landing-hero::before {{
            content:''; position:absolute; top:0;left:0;right:0; height:2px;
            background: linear-gradient(90deg, transparent 5%, #2563EB 35%, #7C3AED 65%, transparent 95%);
            transform-origin: left;
            animation: hero-line-in 0.8s ease-out 0.1s both;
        }}
        /* Orb 1 — blue */
        .lh-orb1 {{
            position:absolute; top:-80px; right:-40px;
            width:420px; height:420px; border-radius:50%;
            background: radial-gradient(circle, rgba(37,99,235,0.18) 0%, transparent 65%);
            animation: hero-orb-1 8s ease-in-out infinite;
            pointer-events:none;
        }}
        /* Orb 2 — purple */
        .lh-orb2 {{
            position:absolute; bottom:-100px; left:10%;
            width:360px; height:360px; border-radius:50%;
            background: radial-gradient(circle, rgba(124,58,237,0.14) 0%, transparent 65%);
            animation: hero-orb-2 10s ease-in-out infinite;
            pointer-events:none;
        }}
        /* Orb 3 — cyan accent */
        .lh-orb3 {{
            position:absolute; top:30%; right:25%;
            width:200px; height:200px; border-radius:50%;
            background: radial-gradient(circle, rgba(6,182,212,0.07) 0%, transparent 65%);
            pointer-events:none;
        }}
        /* Floating particles */
        .lh-particle {{
            position:absolute; width:3px; height:3px;
            border-radius:50%; background:#60A5FA;
            animation: hero-particle linear infinite;
            pointer-events:none;
        }}
        /* Content */
        .lh-eyebrow {{
            font-size:0.68rem; font-weight:700; color:#60A5FA;
            text-transform:uppercase; letter-spacing:0.2em;
            margin-bottom:1rem;
            animation: hero-fade-up 0.5s ease-out 0.2s both;
        }}
        .lh-headline {{
            font-size: clamp(2rem, 4vw, 3.2rem);
            font-weight: 900;
            letter-spacing: -0.05em;
            line-height: 1.1;
            color: #F8FAFC;
            margin-bottom: 1.1rem;
            animation: hero-fade-up 0.5s ease-out 0.3s both;
        }}
        .lh-headline span {{
            background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 60%, #06B6D4 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .lh-sub {{
            font-size: 1rem; color: #94A3B8; line-height: 1.7;
            max-width: 560px; margin-bottom: 2rem;
            animation: hero-fade-up 0.5s ease-out 0.4s both;
        }}
        /* CTA row */
        .lh-cta-row {{
            display:flex; align-items:center; gap:1rem; flex-wrap:wrap;
            margin-bottom: 2.5rem;
            animation: hero-fade-up 0.5s ease-out 0.5s both;
        }}
        /* Stats row */
        .lh-stats {{
            display:flex; gap:2.5rem; flex-wrap:wrap;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            animation: stat-in 0.6s ease-out 0.7s both;
        }}
        .lh-stat-val {{
            font-size:1.5rem; font-weight:900; color:#F8FAFC;
            letter-spacing:-0.03em; line-height:1;
        }}
        .lh-stat-lbl {{
            font-size:0.75rem; color:#64748B; margin-top:0.2rem;
        }}
        .hero-status {{
            display:inline-flex; align-items:center; gap:0.5rem;
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.07);
            border-radius:100px; padding:0.35rem 0.9rem;
            font-size:0.78rem; color:#64748B;
        }}
        .hero-status-dot {{
            width:7px; height:7px; background:#22C55E; border-radius:50%;
            flex-shrink:0; box-shadow:0 0 6px rgba(34,197,94,0.7);
            animation: hero-dot-pulse 2s ease infinite;
        }}
        @keyframes hero-dot-pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.4}} }}
        .hero-status-sep {{ opacity:0.3; }}
        </style>

        <div class="landing-hero">
          <div class="lh-orb1"></div>
          <div class="lh-orb2"></div>
          <div class="lh-orb3"></div>

          <!-- Floating particles -->
          <div class="lh-particle" style="left:15%;bottom:20%;animation-duration:6s;animation-delay:0s;"></div>
          <div class="lh-particle" style="left:28%;bottom:10%;animation-duration:8s;animation-delay:1.5s;opacity:0.4;"></div>
          <div class="lh-particle" style="left:8%;bottom:35%;animation-duration:7s;animation-delay:3s;width:2px;height:2px;"></div>
          <div class="lh-particle" style="left:40%;bottom:5%;animation-duration:9s;animation-delay:0.8s;background:#A78BFA;"></div>
          <div class="lh-particle" style="left:55%;bottom:15%;animation-duration:6.5s;animation-delay:2.2s;background:#06B6D4;width:2px;height:2px;"></div>

          <div class="lh-eyebrow">AI Interview Coach · Powered by Llama 3.3 70B</div>

          <div class="lh-headline">
            Land Your Next<br>
            <span>Tech Role.</span>
          </div>

          <div class="lh-sub">
            Practice interviews with an AI recruiter that evaluates your answers in real-time,
            identifies skill gaps, and builds a personalised improvement plan — so you walk
            into every interview ready.
          </div>

          {status_html}

          <div class="lh-stats">
            <div>
              <div class="lh-stat-val">15,000+</div>
              <div class="lh-stat-lbl">Questions Generated</div>
            </div>
            <div>
              <div class="lh-stat-val">2,500+</div>
              <div class="lh-stat-lbl">Mock Interviews</div>
            </div>
            <div>
              <div class="lh-stat-val">89%</div>
              <div class="lh-stat-lbl">User Improvement Rate</div>
            </div>
            <div>
              <div class="lh-stat-val">5</div>
              <div class="lh-stat-lbl">Target Roles</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Empty state
# ─────────────────────────────────────────────────────────────────────────────
def _render_empty_state():
    st.markdown(
        """
        <div class="empty-state">
          <div class="empty-state-icon">🎯</div>
          <div class="empty-state-title">No interviews yet</div>
          <div class="empty-state-sub">
            Complete your first AI-powered interview to unlock your performance
            dashboard, skill radar, and improvement insights.
          </div>
          <div style="display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-bottom:2rem;">
            <div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);
                        border-radius:14px;padding:1.1rem 1.25rem;text-align:left;width:170px;
                        transition:border-color 0.25s,transform 0.25s;">
              <div style="font-size:0.65rem;font-weight:700;color:#2563EB;text-transform:uppercase;
                          letter-spacing:0.12em;margin-bottom:0.4rem;">Step 01</div>
              <div style="font-size:0.85rem;font-weight:600;color:#CBD5E1;margin-bottom:0.25rem;">Choose a Role</div>
              <div style="font-size:0.75rem;color:#64748B;line-height:1.5;">Pick the job title you're preparing for</div>
            </div>
            <div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);
                        border-radius:14px;padding:1.1rem 1.25rem;text-align:left;width:170px;
                        transition:border-color 0.25s,transform 0.25s;">
              <div style="font-size:0.65rem;font-weight:700;color:#2563EB;text-transform:uppercase;
                          letter-spacing:0.12em;margin-bottom:0.4rem;">Step 02</div>
              <div style="font-size:0.85rem;font-weight:600;color:#CBD5E1;margin-bottom:0.25rem;">Answer Questions</div>
              <div style="font-size:0.75rem;color:#64748B;line-height:1.5;">Respond to AI-generated technical questions</div>
            </div>
            <div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);
                        border-radius:14px;padding:1.1rem 1.25rem;text-align:left;width:170px;
                        transition:border-color 0.25s,transform 0.25s;">
              <div style="font-size:0.65rem;font-weight:700;color:#2563EB;text-transform:uppercase;
                          letter-spacing:0.12em;margin-bottom:0.4rem;">Step 03</div>
              <div style="font-size:0.85rem;font-weight:600;color:#CBD5E1;margin-bottom:0.25rem;">Get Your Score</div>
              <div style="font-size:0.75rem;color:#64748B;line-height:1.5;">Receive detailed feedback and a hiring recommendation</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if st.button("Start Your First Interview →", type="primary", use_container_width=True):
            st.session_state.active_page = "Interview"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  KPI cards
# ─────────────────────────────────────────────────────────────────────────────
def _render_kpi_cards(stats: dict):
    total   = stats.get("total_interviews", 0)
    avg     = stats.get("avg_score") or 0.0
    best    = stats.get("best_score") or 0.0
    weakest = stats.get("weakest_area") or "N/A"
    avg_tech = stats.get("avg_technical") or 0.0

    # Improvement rate: ratio of best to avg (capped at 100 %)
    improvement = round(min((best / avg * 100) - 100, 99), 0) if avg > 0 else 0

    cards = [
        {
            "icon": "🎯",
            "label": "Total Interviews",
            "value": str(total),
            "sub": "sessions completed",
            "accent": "#3B82F6",
            "glow": "rgba(59,130,246,0.15)",
            "icon_bg": "rgba(59,130,246,0.12)",
            "icon_border": "rgba(59,130,246,0.22)",
        },
        {
            "icon": "⭐",
            "label": "Average Score",
            "value": f"{avg}",
            "sub": "out of 10",
            "accent": "#22C55E",
            "glow": "rgba(34,197,94,0.12)",
            "icon_bg": "rgba(34,197,94,0.1)",
            "icon_border": "rgba(34,197,94,0.2)",
        },
        {
            "icon": "🏆",
            "label": "Best Score",
            "value": f"{best}",
            "sub": "personal best",
            "accent": "#F59E0B",
            "glow": "rgba(245,158,11,0.12)",
            "icon_bg": "rgba(245,158,11,0.1)",
            "icon_border": "rgba(245,158,11,0.2)",
        },
        {
            "icon": "🎓",
            "label": "Focus Area",
            "value": weakest,
            "sub": "needs most work",
            "accent": "#A78BFA",
            "glow": "rgba(167,139,250,0.12)",
            "icon_bg": "rgba(124,58,237,0.1)",
            "icon_border": "rgba(124,58,237,0.2)",
        },
        {
            "icon": "⚡",
            "label": "Technical Avg",
            "value": f"{avg_tech}",
            "sub": "technical score",
            "accent": "#06B6D4",
            "glow": "rgba(6,182,212,0.12)",
            "icon_bg": "rgba(6,182,212,0.1)",
            "icon_border": "rgba(6,182,212,0.2)",
        },
    ]

    cols = st.columns(5, gap="small")
    for col, card in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card" style="
                    --kpi-accent: {card['accent']};
                    --kpi-glow:   {card['glow']};
                    --kpi-icon-bg:     {card['icon_bg']};
                    --kpi-icon-border: {card['icon_border']};
                ">
                  <div class="kpi-top">
                    <div class="kpi-icon">{card['icon']}</div>
                  </div>
                  <div class="kpi-value" style="color:{card['accent']}">{card['value']}</div>
                  <div class="kpi-label">{card['label']}</div>
                  <div style="font-size:0.68rem;color:var(--text-4);margin-top:0.15rem;">{card['sub']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
#  DataFrame builder
# ─────────────────────────────────────────────────────────────────────────────
def _build_dataframe(analytics: list) -> pd.DataFrame:
    df = pd.DataFrame(analytics)
    if "started_at" in df.columns:
        df["date"] = pd.to_datetime(df["started_at"]).dt.strftime("%b %d")
    elif "recorded_at" in df.columns:
        df["date"] = pd.to_datetime(df["recorded_at"]).dt.strftime("%b %d")
    else:
        df["date"] = [str(i) for i in range(1, len(df) + 1)]
    df["interview_num"] = range(1, len(df) + 1)
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Shared Plotly layout
# ─────────────────────────────────────────────────────────────────────────────
def _chart_layout(**kwargs) -> dict:
    base = dict(
        paper_bgcolor="transparent",
        plot_bgcolor="transparent",
        font=dict(color="#94A3B8", family="Inter, sans-serif", size=11),
        margin=dict(l=8, r=8, t=28, b=28),
        hoverlabel=dict(
            bgcolor="#0d1b2e",
            bordercolor="rgba(255,255,255,0.1)",
            font=dict(color="#F8FAFC", size=12),
        ),
    )
    base.update(kwargs)
    return base


def _score_to_color(score: float) -> str:
    if score >= 8:   return "#22C55E"
    if score >= 6:   return "#3B82F6"
    if score >= 4:   return "#F59E0B"
    return "#EF4444"


# ─────────────────────────────────────────────────────────────────────────────
#  Trend chart
# ─────────────────────────────────────────────────────────────────────────────
def _render_trend_chart(df: pd.DataFrame):
    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Performance Trend</div>'
        '<div class="chart-sub">Overall score across sessions</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()

    # Gradient fill area under the overall line
    if "overall_score" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["interview_num"], y=df["overall_score"],
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.07)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False, hoverinfo="skip",
        ))

    traces = [
        ("overall_score", "Overall",       "#3B82F6", True,  3),
        ("technical",     "Technical",     "#22C55E", False, 1.5),
        ("communication", "Communication", "#F59E0B", False, 1.5),
        ("problem_solving","Problem Solving","#A78BFA",False, 1.5),
        ("confidence",    "Confidence",    "#06B6D4", False, 1.5),
    ]
    for col, name, color, visible, width in traces:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["interview_num"],
                y=df[col],
                name=name,
                mode="lines+markers",
                line=dict(color=color, width=width),
                marker=dict(size=6 if visible else 4,
                            color=color,
                            line=dict(width=1.5, color="#020617")),
                visible=True if visible else "legendonly",
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}/10<extra></extra>",
            ))

    fig.update_layout(
        **_chart_layout(
            yaxis=dict(range=[0, 10.5], dtick=2,
                       gridcolor="rgba(255,255,255,0.04)",
                       tickfont=dict(size=10)),
            xaxis=dict(title="Session",
                       gridcolor="rgba(255,255,255,0.03)",
                       tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
            height=290,
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Skill radar
# ─────────────────────────────────────────────────────────────────────────────
def _render_skill_radar(df: pd.DataFrame):
    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Skill Radar</div>'
        '<div class="chart-sub">Average across all sessions</div>',
        unsafe_allow_html=True,
    )

    cats    = ["Technical", "Communication", "Problem Solving", "Confidence", "Completeness"]
    col_map = ["technical",  "communication",  "problem_solving",  "confidence",  "completeness"]
    avgs    = [round(float(df[c].mean()), 1) if c in df.columns else 0.0 for c in col_map]

    fig = go.Figure()

    # Subtle background fill showing max
    fig.add_trace(go.Scatterpolar(
        r=[10] * len(cats) + [10],
        theta=cats + [cats[0]],
        fill="toself",
        fillcolor="rgba(255,255,255,0.015)",
        line=dict(color="rgba(255,255,255,0.04)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    # Actual scores
    fig.add_trace(go.Scatterpolar(
        r=avgs + [avgs[0]],
        theta=cats + [cats[0]],
        fill="toself",
        fillcolor="rgba(37,99,235,0.18)",
        line=dict(color="#3B82F6", width=2.5),
        marker=dict(size=6, color="#60A5FA"),
        name="Average",
        hovertemplate="<b>%{theta}</b>: %{r:.1f}/10<extra></extra>",
    ))

    fig.update_layout(
        **_chart_layout(
            polar=dict(
                bgcolor="transparent",
                radialaxis=dict(
                    range=[0, 10], showticklabels=True,
                    tickfont=dict(size=9, color="#475569"),
                    gridcolor="rgba(255,255,255,0.05)",
                    linecolor="rgba(255,255,255,0.04)",
                    dtick=5,
                ),
                angularaxis=dict(
                    gridcolor="rgba(255,255,255,0.06)",
                    tickfont=dict(size=11, color="#94A3B8"),
                    linecolor="rgba(255,255,255,0.04)",
                ),
            ),
            showlegend=False,
            height=290,
            margin=dict(l=30, r=30, t=28, b=28),
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Score distribution histogram
# ─────────────────────────────────────────────────────────────────────────────
def _render_score_distribution(df: pd.DataFrame):
    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Score Distribution</div>'
        '<div class="chart-sub">How your scores are spread</div>',
        unsafe_allow_html=True,
    )

    if "overall_score" in df.columns:
        colors = df["overall_score"].apply(_score_to_color).tolist()
        fig = go.Figure(go.Bar(
            x=df["overall_score"].round(0),
            y=[1] * len(df),
            marker=dict(
                color=colors,
                line=dict(width=0),
                opacity=0.85,
            ),
            hovertemplate="Score: %{x:.1f}<extra></extra>",
        ))
        fig.update_layout(
            **_chart_layout(
                bargap=0.18,
                xaxis=dict(title="Score", range=[0, 10.2],
                           gridcolor="rgba(255,255,255,0.03)",
                           tickfont=dict(size=10)),
                yaxis=dict(title="Sessions",
                           gridcolor="rgba(255,255,255,0.03)",
                           tickfont=dict(size=10)),
                height=270,
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Role breakdown donut
# ─────────────────────────────────────────────────────────────────────────────
def _render_role_breakdown(df: pd.DataFrame):
    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Practice by Role</div>'
        '<div class="chart-sub">Sessions per target role</div>',
        unsafe_allow_html=True,
    )

    if "role" in df.columns:
        counts = df["role"].value_counts().reset_index()
        counts.columns = ["role", "count"]

        fig = px.pie(
            counts,
            values="count",
            names="role",
            hole=0.62,
            color_discrete_sequence=["#3B82F6","#22C55E","#F59E0B","#A78BFA","#06B6D4"],
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{value} session(s)<br>%{percent}<extra></extra>",
            marker=dict(line=dict(color="#020617", width=2)),
        )
        fig.update_layout(
            **_chart_layout(
                legend=dict(
                    orientation="v", x=1.0, y=0.5,
                    font=dict(size=10, color="#94A3B8"),
                    bgcolor="transparent",
                ),
                height=270,
                margin=dict(l=0, r=80, t=28, b=28),
            )
        )
        # Centre label
        fig.add_annotation(
            text=f"<b>{len(df)}</b><br><span style='font-size:10px'>Sessions</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#F8FAFC"),
            xref="paper", yref="paper",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Recent interviews table
# ─────────────────────────────────────────────────────────────────────────────
_REC_BADGE = {
    "Needs Improvement":  ("rgba(239,68,68,0.12)",  "#EF4444"),
    "Ready for Internship":("rgba(245,158,11,0.12)","#F59E0B"),
    "Entry-Level Ready":  ("rgba(59,130,246,0.12)", "#3B82F6"),
    "Strong Candidate":   ("rgba(34,197,94,0.12)",  "#22C55E"),
    "Senior Ready":       ("rgba(167,139,250,0.12)","#A78BFA"),
}

def _render_recent_interviews(session_id: str):
    interviews = db.get_user_interviews(session_id, limit=8)
    if not interviews:
        return

    # Section header
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
        '<div>'
        '<div style="font-size:1rem;font-weight:700;color:#F8FAFC;letter-spacing:-0.02em;">Recent Sessions</div>'
        '<div style="font-size:0.75rem;color:#64748B;margin-top:0.15rem;">Your last completed interviews</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Table header
    st.markdown(
        """
        <div class="data-table">
          <div class="t-head" style="grid-template-columns:2fr 1fr 1fr 2.2fr 1.2fr;">
            <div class="th">Role</div>
            <div class="th">Level</div>
            <div class="th">Score</div>
            <div class="th">Recommendation</div>
            <div class="th">Date</div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    for iv in interviews:
        score = iv.get("overall_score") or 0
        rec   = iv.get("hiring_recommendation") or "—"
        date  = (iv.get("started_at") or "")[:10]
        sc    = _score_to_color(score)
        diff  = iv.get("difficulty", "—")

        bg_c, fg_c = _REC_BADGE.get(rec, ("rgba(100,116,139,0.12)", "#64748B"))

        st.markdown(
            f"""
            <div class="t-row" style="grid-template-columns:2fr 1fr 1fr 2.2fr 1.2fr;">
              <div class="td bold">{iv.get('role','')}</div>
              <div class="td">{diff}</div>
              <div class="td bold" style="color:{sc};">{score}/10</div>
              <div class="td">
                <span style="background:{bg_c};color:{fg_c};border:1px solid {fg_c}30;
                             border-radius:100px;padding:0.2rem 0.75rem;
                             font-size:0.72rem;font-weight:600;">{rec}</span>
              </div>
              <div class="td muted">{date}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
