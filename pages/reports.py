"""
Reports Page — Detailed interview history and individual report drilldown.
"""

import streamlit as st
import plotly.graph_objects as go
import json
from database import database as db


def render():
    st.markdown('<h1 class="page-title">📋 Interview Reports</h1>', unsafe_allow_html=True)

    session_id = st.session_state.get("session_id", "default")
    interviews = db.get_user_interviews(session_id, limit=50)

    if not interviews:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-title">No Reports Yet</div>
                <div class="empty-subtitle">Complete an interview to see your detailed reports here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start an Interview →", type="primary"):
            st.session_state.active_page = "Interview"
            st.rerun()
        return

    # Interview selector
    interview_labels = []
    for iv in interviews:
        score = iv.get("overall_score") or 0.0
        date = (iv.get("started_at") or "")[:10]
        label = f"{date} — {iv['role']} ({iv['difficulty']}) — {score}/10"
        interview_labels.append(label)

    selected_label = st.selectbox(
        "Select Interview",
        interview_labels,
        index=0,
        label_visibility="collapsed",
    )

    selected_idx = interview_labels.index(selected_label)
    selected_interview = interviews[selected_idx]
    interview_id = selected_interview["id"]

    report = db.get_report(interview_id)
    answers = db.get_interview_answers(interview_id)

    if not report:
        st.warning("Report data not available for this interview.")
        return

    _render_report_header(selected_interview, report)
    st.markdown("<br>", unsafe_allow_html=True)
    _render_score_breakdown(report)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        _render_report_narrative(report)
    with col2:
        _render_score_chart(report)

    st.markdown("### Question-by-Question Breakdown")
    _render_answer_details(answers)


def _render_report_header(interview: dict, report: dict):
    overall = report.get("overall_score", 0)
    rec = report.get("hiring_recommendation", "—")
    date = (interview.get("started_at") or "")[:10]

    rec_colors = {
        "Needs Improvement": "#ef4444",
        "Ready for Internship": "#f59e0b",
        "Entry-Level Ready": "#3b82f6",
        "Strong Candidate": "#10b981",
        "Senior Ready": "#8b5cf6",
    }
    rec_color = rec_colors.get(rec, "#94a3b8")
    score_color = _score_color(overall)

    st.markdown(
        f"""
        <div class="report-header-card">
            <div class="rh-left">
                <div class="rh-role">{interview.get('role', '')}</div>
                <div class="rh-meta">{interview.get('difficulty', '')} · {interview.get('total_questions', '')} Questions · {date}</div>
                <div class="rh-rec" style="color:{rec_color};border-color:{rec_color}40;background:{rec_color}15">{rec}</div>
            </div>
            <div class="rh-right">
                <div class="rh-score" style="color:{score_color}">{overall}</div>
                <div class="rh-score-label">/ 10</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_score_breakdown(report: dict):
    fields = [
        ("Technical", "technical_avg"),
        ("Communication", "communication_avg"),
        ("Problem Solving", "problem_solving_avg"),
        ("Confidence", "confidence_avg"),
        ("Completeness", "completeness_avg"),
    ]

    st.markdown('<div class="score-breakdown">', unsafe_allow_html=True)
    cols = st.columns(5)
    for col, (label, key) in zip(cols, fields):
        val = report.get(key, 0) or 0
        color = _score_color(val)
        with col:
            pct = int(val * 10)
            st.markdown(
                f"""
                <div class="breakdown-item">
                    <div class="breakdown-score" style="color:{color}">{val}</div>
                    <div class="breakdown-bar-bg">
                        <div class="breakdown-bar-fill" style="width:{pct}%;background:{color}"></div>
                    </div>
                    <div class="breakdown-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_report_narrative(report: dict):
    st.markdown("#### 💪 Strengths")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for s in (report.get("strengths") or []):
        st.markdown(f'<div class="list-item positive">✓ {s}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 🎯 Areas to Improve")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for w in (report.get("improvement_areas") or report.get("weaknesses") or []):
        st.markdown(f'<div class="list-item negative">→ {w}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 📚 Recommended Topics")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    for t in (report.get("recommended_topics") or []):
        st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_score_chart(report: dict):
    st.markdown("#### Score Radar")

    categories = ["Technical", "Communication", "Problem Solving", "Confidence", "Completeness"]
    values = [
        report.get("technical_avg") or 0,
        report.get("communication_avg") or 0,
        report.get("problem_solving_avg") or 0,
        report.get("confidence_avg") or 0,
        report.get("completeness_avg") or 0,
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(59,130,246,0.25)",
        line=dict(color="#3b82f6", width=2),
        name="Score",
    ))
    fig.update_layout(
        paper_bgcolor="transparent",
        plot_bgcolor="transparent",
        font=dict(color="#e2e8f0"),
        polar=dict(
            bgcolor="transparent",
            radialaxis=dict(range=[0, 10], gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=9, color="#94a3b8")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=11, color="#e2e8f0")),
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Assessment Summary")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<p class="summary-text">{report.get("summary", "No summary available.")}</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_answer_details(answers: list):
    if not answers:
        st.info("No answers recorded for this interview.")
        return

    for ans in answers:
        q_num = ans.get("question_num", "?")
        q_text = ans.get("question_text", "")
        a_text = ans.get("answer_text", "")
        overall = ans.get("overall", 0)
        feedback = ans.get("feedback", "")
        score_color = _score_color(overall)

        with st.expander(f"Question {q_num}  —  Score: {overall}/10  —  {q_text[:80]}..."):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("**Question:**")
                st.markdown(f'<div class="question-text-sm">{q_text}</div>', unsafe_allow_html=True)
                st.markdown("**Your Answer:**")
                st.markdown(f'<div class="answer-text">{a_text}</div>', unsafe_allow_html=True)

            with col2:
                # Mini score bars
                score_fields = [
                    ("Technical", "technical"),
                    ("Communication", "communication"),
                    ("Problem Solving", "problem_solving"),
                    ("Confidence", "confidence"),
                    ("Completeness", "completeness"),
                ]
                for label, key in score_fields:
                    val = ans.get(key, 0)
                    color = _score_color(val)
                    pct = int(val * 10)
                    st.markdown(
                        f'<div class="mini-score-row">'
                        f'<span class="mini-label">{label}</span>'
                        f'<div class="mini-bar-bg"><div class="mini-bar-fill" style="width:{pct}%;background:{color}"></div></div>'
                        f'<span class="mini-val" style="color:{color}">{val}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            if feedback:
                st.markdown("**Feedback:**")
                st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)

            # Strengths / Improvements
            try:
                strengths = json.loads(ans.get("strengths") or "[]")
                improvements = json.loads(ans.get("improvements") or "[]")
            except Exception:
                strengths, improvements = [], []

            if strengths or improvements:
                sc1, sc2 = st.columns(2)
                with sc1:
                    if strengths:
                        st.markdown("**Strengths:**")
                        for s in strengths:
                            st.markdown(f'<div class="list-item positive small">✓ {s}</div>', unsafe_allow_html=True)
                with sc2:
                    if improvements:
                        st.markdown("**Improvements:**")
                        for i in improvements:
                            st.markdown(f'<div class="list-item negative small">→ {i}</div>', unsafe_allow_html=True)


def _score_color(score: float) -> str:
    if score >= 8:
        return "#10b981"
    elif score >= 6:
        return "#3b82f6"
    elif score >= 4:
        return "#f59e0b"
    return "#ef4444"
