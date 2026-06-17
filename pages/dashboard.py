"""
Dashboard Page — KPI cards, performance trends, and analytics charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from database import database as db


def render():
    st.markdown('<h1 class="page-title">📊 Dashboard</h1>', unsafe_allow_html=True)

    session_id = st.session_state.get("session_id", "default")
    stats = db.get_dashboard_stats(session_id)
    analytics = db.get_analytics(session_id)

    if not analytics:
        _render_empty_state()
        return

    _render_kpi_cards(stats)
    st.markdown("<br>", unsafe_allow_html=True)

    df = _build_dataframe(analytics)

    col1, col2 = st.columns(2)
    with col1:
        _render_trend_chart(df)
    with col2:
        _render_skill_radar(df)

    col3, col4 = st.columns(2)
    with col3:
        _render_score_distribution(df)
    with col4:
        _render_role_breakdown(df)

    _render_recent_interviews(session_id)


def _render_empty_state():
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🎯</div>
            <div class="empty-title">No Interviews Yet</div>
            <div class="empty-subtitle">Complete your first interview to see your dashboard analytics.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start Your First Interview →", type="primary"):
        st.session_state.active_page = "Interview"
        st.rerun()


def _render_kpi_cards(stats: dict):
    total = stats.get("total_interviews", 0)
    avg = stats.get("avg_score") or 0.0
    best = stats.get("best_score") or 0.0
    weakest = stats.get("weakest_area", "N/A")

    cards = [
        {"icon": "🎯", "label": "Total Interviews", "value": str(total), "color": "#3b82f6"},
        {"icon": "⭐", "label": "Average Score", "value": f"{avg}/10", "color": "#10b981"},
        {"icon": "🏆", "label": "Best Score", "value": f"{best}/10", "color": "#f59e0b"},
        {"icon": "🎯", "label": "Focus Area", "value": weakest, "color": "#8b5cf6"},
    ]

    cols = st.columns(4)
    for col, card in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon" style="color:{card['color']}">{card['icon']}</div>
                    <div class="kpi-value" style="color:{card['color']}">{card['value']}</div>
                    <div class="kpi-label">{card['label']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _build_dataframe(analytics: list) -> pd.DataFrame:
    df = pd.DataFrame(analytics)
    if "started_at" in df.columns:
        df["date"] = pd.to_datetime(df["started_at"]).dt.strftime("%m/%d")
    elif "recorded_at" in df.columns:
        df["date"] = pd.to_datetime(df["recorded_at"]).dt.strftime("%m/%d")
    else:
        df["date"] = range(1, len(df) + 1)
    df["interview_num"] = range(1, len(df) + 1)
    return df


def _render_trend_chart(df: pd.DataFrame):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Performance Trend")

    fig = go.Figure()

    metrics = [
        ("overall_score", "Overall", "#3b82f6", True),
        ("technical", "Technical", "#10b981", False),
        ("communication", "Communication", "#f59e0b", False),
        ("problem_solving", "Problem Solving", "#8b5cf6", False),
    ]

    for col, name, color, visible in metrics:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["interview_num"],
                y=df[col],
                name=name,
                line=dict(color=color, width=2.5 if visible else 1.5),
                visible=True if visible else "legendonly",
                mode="lines+markers",
                marker=dict(size=6),
            ))

    fig.update_layout(
        **_chart_layout(),
        yaxis=dict(range=[0, 10.5], dtick=2, gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(title="Interview #", gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", y=-0.2),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_skill_radar(df: pd.DataFrame):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Skill Radar")

    categories = ["Technical", "Communication", "Problem Solving", "Confidence", "Completeness"]
    col_map = ["technical", "communication", "problem_solving", "confidence", "completeness"]

    avgs = [round(df[c].mean(), 1) if c in df.columns else 0 for c in col_map]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=avgs + [avgs[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(59,130,246,0.2)",
        line=dict(color="#3b82f6", width=2),
        name="Average",
    ))
    fig.update_layout(
        **_chart_layout(),
        polar=dict(
            bgcolor="transparent",
            radialaxis=dict(range=[0, 10], gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=10, color="#94a3b8")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=11, color="#e2e8f0")),
        ),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_score_distribution(df: pd.DataFrame):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Score Distribution")

    if "overall_score" in df.columns:
        fig = go.Figure(go.Histogram(
            x=df["overall_score"],
            nbinsx=10,
            marker=dict(
                color=df["overall_score"].apply(_score_to_color),
                line=dict(width=1, color="rgba(0,0,0,0.2)"),
            ),
            xbins=dict(start=0, end=10, size=1),
        ))
        fig.update_layout(
            **_chart_layout(),
            xaxis=dict(title="Score", range=[0, 10]),
            yaxis=dict(title="Count"),
            height=280,
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_role_breakdown(df: pd.DataFrame):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Interviews by Role")

    if "role" in df.columns:
        role_counts = df["role"].value_counts().reset_index()
        role_counts.columns = ["role", "count"]

        fig = px.pie(
            role_counts,
            values="count",
            names="role",
            color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"],
            hole=0.5,
        )
        fig.update_layout(
            **_chart_layout(),
            legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
            height=280,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_recent_interviews(session_id: str):
    st.markdown("### Recent Interviews")
    interviews = db.get_user_interviews(session_id, limit=10)

    if not interviews:
        return

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    header_cols = st.columns([2, 1, 1, 2, 2])
    headers = ["Role", "Difficulty", "Score", "Recommendation", "Date"]
    for col, h in zip(header_cols, headers):
        col.markdown(f'<div class="table-header">{h}</div>', unsafe_allow_html=True)

    for interview in interviews:
        score = interview.get("overall_score") or 0
        rec = interview.get("hiring_recommendation") or "—"
        date_str = interview.get("started_at", "")[:10]
        color = _score_to_color(score)

        row_cols = st.columns([2, 1, 1, 2, 2])
        row_cols[0].markdown(f'<div class="table-cell">{interview.get("role", "")}</div>', unsafe_allow_html=True)
        row_cols[1].markdown(f'<div class="table-cell">{interview.get("difficulty", "")}</div>', unsafe_allow_html=True)
        row_cols[2].markdown(f'<div class="table-cell" style="color:{color};font-weight:600">{score}/10</div>', unsafe_allow_html=True)
        row_cols[3].markdown(f'<div class="table-cell">{rec}</div>', unsafe_allow_html=True)
        row_cols[4].markdown(f'<div class="table-cell muted">{date_str}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _chart_layout() -> dict:
    return dict(
        paper_bgcolor="transparent",
        plot_bgcolor="transparent",
        font=dict(color="#e2e8f0", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=30, b=30),
    )


def _score_to_color(score: float) -> str:
    if score >= 8:
        return "#10b981"
    elif score >= 6:
        return "#3b82f6"
    elif score >= 4:
        return "#f59e0b"
    return "#ef4444"
