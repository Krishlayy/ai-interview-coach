"""
Reports Page — Executive analytics dashboard (Phase 4)
Interview selector · KPI summary · Radar · Trend · Timeline · AI recommendations
"""
import streamlit as st
import plotly.graph_objects as go
import json
from typing import List, Dict, Any

from database import database as db

# ─── colour helper ────────────────────────────────────────────────────────────
def _sc(v: float) -> str:
    if v >= 8: return "#22C55E"
    if v >= 6: return "#3B82F6"
    if v >= 4: return "#F59E0B"
    return "#EF4444"

_REC_PALETTE: Dict[str, tuple] = {
    "Needs Improvement":    ("#EF4444", "rgba(239,68,68,0.1)"),
    "Ready for Internship": ("#F59E0B", "rgba(245,158,11,0.1)"),
    "Entry-Level Ready":    ("#3B82F6", "rgba(59,130,246,0.1)"),
    "Strong Candidate":     ("#22C55E", "rgba(34,197,94,0.1)"),
    "Senior Ready":         ("#A78BFA", "rgba(167,139,250,0.1)"),
}

# ─── base chart layout ────────────────────────────────────────────────────────
def _chart_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor="transparent", plot_bgcolor="transparent",
        font=dict(color="#94A3B8", family="Inter, sans-serif", size=11),
        margin=dict(l=8, r=8, t=24, b=24),
        hoverlabel=dict(
            bgcolor="#0d1b2e", bordercolor="rgba(255,255,255,0.08)",
            font=dict(color="#F8FAFC", size=12),
        ),
    )
    base.update(kw)
    return base


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def render():
    session_id = st.session_state.get("session_id", "default")
    interviews = db.get_user_interviews(session_id, limit=50)

    _render_page_header()

    if not interviews:
        _render_empty_state()
        return

    selected_iv, report, answers = _render_selector(interviews)
    if not report:
        st.warning("Report data is not available for this interview.", icon="⚠️")
        return

    _render_report_hero(selected_iv, report)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _render_kpi_row(report)
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        _render_radar(report)
    with col_r:
        _render_trend(answers)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2], gap="large")
    with col_a:
        _render_strengths_weaknesses(report)
    with col_b:
        _render_ai_recommendations(report)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _render_timeline(answers)

# ─────────────────────────────────────────────────────────────────────────────
#  Page header
# ─────────────────────────────────────────────────────────────────────────────
def _render_page_header():
    st.markdown(
        """
        <div style="margin-bottom:1.75rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#60A5FA;
                      text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.6rem;">
            Performance Reports
          </div>
          <div style="font-size:clamp(1.5rem,2.5vw,2.1rem);font-weight:900;
                      letter-spacing:-0.04em;line-height:1.15;
                      background:linear-gradient(135deg,#F8FAFC 0%,#94A3B8 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text;margin-bottom:0.4rem;">
            Interview Analytics
          </div>
          <div style="font-size:0.9rem;color:#64748B;line-height:1.6;">
            Deep dive into each session — scores, strengths, feedback, and AI recommendations.
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
        <div style="text-align:center;padding:5rem 2rem;">
          <div style="width:72px;height:72px;border-radius:50%;margin:0 auto 1.5rem;
                      background:linear-gradient(135deg,rgba(37,99,235,0.12),rgba(124,58,237,0.12));
                      border:1px solid rgba(37,99,235,0.2);display:flex;
                      align-items:center;justify-content:center;font-size:2rem;">
            📋
          </div>
          <div style="font-size:1.4rem;font-weight:800;color:#F8FAFC;
                      letter-spacing:-0.03em;margin-bottom:0.6rem;">No reports yet</div>
          <div style="font-size:0.9rem;color:#64748B;max-width:380px;
                      margin:0 auto 2rem;line-height:1.65;">
            Complete an interview session to generate your first analytics report.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        if st.button("Start an Interview →", type="primary", use_container_width=True):
            st.session_state.active_page = "Interview"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Interview selector — returns (interview_dict, report_dict, answers_list)
# ─────────────────────────────────────────────────────────────────────────────
def _render_selector(interviews: List[Dict]):
    labels = []
    for iv in interviews:
        score = iv.get("overall_score") or 0.0
        date  = (iv.get("started_at") or "")[:10]
        labels.append(f"{date}  ·  {iv['role']}  ·  {iv['difficulty']}  ·  {score}/10")

    chosen = st.selectbox(
        "Select a session to analyse",
        labels,
        index=0,
        label_visibility="visible",
    )
    idx        = labels.index(chosen)
    iv         = interviews[idx]
    report     = db.get_report(iv["id"])
    answers    = db.get_interview_answers(iv["id"])
    return iv, report, answers

# ─────────────────────────────────────────────────────────────────────────────
#  Report hero banner
# ─────────────────────────────────────────────────────────────────────────────
def _render_report_hero(iv: dict, report: dict):
    overall = report.get("overall_score") or 0
    rec     = report.get("hiring_recommendation") or "—"
    date    = (iv.get("started_at") or "")[:10]
    role    = iv.get("role", "—")
    diff    = iv.get("difficulty", "—")
    n_q     = iv.get("total_questions", "—")
    sc      = _sc(overall)
    fg, bg  = _REC_PALETTE.get(rec, ("#94A3B8", "rgba(148,163,184,0.1)"))

    st.markdown(
        f"""
        <div class="report-hdr">
          <div>
            <div class="rh2-role">{role}</div>
            <div class="rh2-meta">{diff} level &nbsp;·&nbsp; {n_q} questions &nbsp;·&nbsp; {date}</div>
            <div class="rh2-badge"
                 style="color:{fg};border-color:{fg}35;background:{bg};">
              {rec}
            </div>
          </div>
          <div style="text-align:right;">
            <div class="rh2-score" style="color:{sc};">{overall}</div>
            <div class="rh2-denom">/ 10</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  KPI summary row (5 metric tiles)
# ─────────────────────────────────────────────────────────────────────────────
def _render_kpi_row(report: dict):
    fields = [
        ("Technical",       "technical_avg",       "#3B82F6", "rgba(59,130,246,0.1)",   "rgba(59,130,246,0.18)"),
        ("Communication",   "communication_avg",    "#22C55E", "rgba(34,197,94,0.1)",    "rgba(34,197,94,0.18)"),
        ("Problem Solving", "problem_solving_avg",  "#F59E0B", "rgba(245,158,11,0.1)",   "rgba(245,158,11,0.18)"),
        ("Confidence",      "confidence_avg",       "#A78BFA", "rgba(167,139,250,0.1)",  "rgba(167,139,250,0.18)"),
        ("Completeness",    "completeness_avg",     "#06B6D4", "rgba(6,182,212,0.1)",    "rgba(6,182,212,0.18)"),
    ]
    cols = st.columns(5, gap="small")
    for col, (label, key, accent, icon_bg, icon_border) in zip(cols, fields):
        val = report.get(key) or 0
        bar = int(val * 10)
        sc  = _sc(val)
        with col:
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,rgba(13,27,46,0.95),rgba(7,16,41,0.98));
                            border:1px solid rgba(255,255,255,0.06);border-radius:16px;
                            padding:1.25rem 1rem;position:relative;overflow:hidden;
                            transition:all 0.25s ease;">
                  <div style="font-size:0.68rem;font-weight:700;color:#64748B;
                              text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.6rem;">
                    {label}
                  </div>
                  <div style="font-size:1.9rem;font-weight:900;color:{sc};
                              letter-spacing:-0.04em;line-height:1;margin-bottom:0.5rem;">
                    {val}
                  </div>
                  <div style="height:4px;background:rgba(255,255,255,0.05);
                              border-radius:2px;overflow:hidden;">
                    <div style="height:100%;width:{bar}%;background:{accent};
                                border-radius:2px;"></div>
                  </div>
                  <div style="font-size:0.65rem;color:#334155;margin-top:0.35rem;">out of 10</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
#  Skill radar chart
# ─────────────────────────────────────────────────────────────────────────────
def _render_radar(report: dict):
    cats = ["Technical","Communication","Problem Solving","Confidence","Completeness"]
    vals = [
        report.get("technical_avg") or 0,
        report.get("communication_avg") or 0,
        report.get("problem_solving_avg") or 0,
        report.get("confidence_avg") or 0,
        report.get("completeness_avg") or 0,
    ]

    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Skill Radar</div>'
        '<div class="chart-sub">Performance across all dimensions</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()

    # Max boundary ring
    fig.add_trace(go.Scatterpolar(
        r=[10]*len(cats)+[10], theta=cats+[cats[0]],
        fill="toself", fillcolor="rgba(255,255,255,0.015)",
        line=dict(color="rgba(255,255,255,0.04)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    # Actual scores
    fig.add_trace(go.Scatterpolar(
        r=vals+[vals[0]], theta=cats+[cats[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.2)",
        line=dict(color="#3B82F6", width=2.5),
        marker=dict(size=6, color="#60A5FA",
                    line=dict(width=1.5, color="#020617")),
        name="Score",
        hovertemplate="<b>%{theta}</b>: %{r:.1f}/10<extra></extra>",
    ))

    fig.update_layout(
        **_chart_layout(
            polar=dict(
                bgcolor="transparent",
                radialaxis=dict(
                    range=[0,10], dtick=5, showticklabels=True,
                    tickfont=dict(size=9, color="#475569"),
                    gridcolor="rgba(255,255,255,0.05)",
                    linecolor="rgba(255,255,255,0.04)",
                ),
                angularaxis=dict(
                    gridcolor="rgba(255,255,255,0.06)",
                    tickfont=dict(size=11, color="#94A3B8"),
                    linecolor="rgba(255,255,255,0.04)",
                ),
            ),
            showlegend=False,
            height=310,
            margin=dict(l=30, r=30, t=24, b=24),
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Per-question score trend line
# ─────────────────────────────────────────────────────────────────────────────
def _render_trend(answers: list):
    st.markdown(
        '<div class="chart-wrap">'
        '<div class="chart-title">Answer Quality Trend</div>'
        '<div class="chart-sub">Score progression through the session</div>',
        unsafe_allow_html=True,
    )

    if not answers:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;color:#334155;'
            'font-size:0.85rem;">No answers recorded</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    q_nums  = [a.get("question_num", i+1) for i, a in enumerate(answers)]
    overall = [float(a.get("overall", 0)) for a in answers]
    tech    = [float(a.get("technical", 0)) for a in answers]
    comm    = [float(a.get("communication", 0)) for a in answers]

    fig = go.Figure()

    # Gradient fill under overall
    fig.add_trace(go.Scatter(
        x=q_nums, y=overall,
        fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ))

    traces = [
        (q_nums, overall, "Overall",       "#3B82F6", 2.5, True),
        (q_nums, tech,    "Technical",     "#22C55E", 1.5, False),
        (q_nums, comm,    "Communication", "#F59E0B", 1.5, False),
    ]
    for x, y, name, color, width, vis in traces:
        fig.add_trace(go.Scatter(
            x=x, y=y, name=name,
            mode="lines+markers",
            line=dict(color=color, width=width),
            marker=dict(size=7 if vis else 5, color=color,
                        line=dict(width=1.5, color="#020617")),
            visible=True if vis else "legendonly",
            hovertemplate=f"<b>Q%{{x}}</b> · {name}: %{{y:.1f}}/10<extra></extra>",
        ))

    fig.update_layout(
        **_chart_layout(
            yaxis=dict(range=[0,10.5], dtick=2,
                       gridcolor="rgba(255,255,255,0.04)",
                       tickfont=dict(size=10)),
            xaxis=dict(title="Question",
                       tickmode="array", tickvals=q_nums,
                       gridcolor="rgba(255,255,255,0.03)",
                       tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
            height=310,
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Strengths & weaknesses panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_strengths_weaknesses(report: dict):
    strengths  = report.get("strengths") or []
    areas      = report.get("improvement_areas") or report.get("weaknesses") or []
    summary    = report.get("summary") or "No summary available."

    # Section title
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">'
        'Assessment Breakdown</div>',
        unsafe_allow_html=True,
    )

    # Strengths card
    s_items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:0.6rem;'
        f'padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.025);">'
        f'<div style="width:6px;height:6px;border-radius:50%;background:#22C55E;'
        f'flex-shrink:0;margin-top:0.45rem;"></div>'
        f'<div style="font-size:0.875rem;color:#CBD5E1;line-height:1.55;">{s}</div>'
        f'</div>'
        for s in strengths
    ) or '<div style="color:#334155;font-size:0.85rem;">None recorded</div>'

    st.markdown(
        f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:14px;padding:1.1rem 1.25rem;margin-bottom:0.75rem;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#22C55E;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.65rem;">'
        f'Strengths</div>{s_items}</div>',
        unsafe_allow_html=True,
    )

    # Improvement areas card
    a_items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:0.6rem;'
        f'padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.025);">'
        f'<div style="width:6px;height:6px;border-radius:50%;background:#F59E0B;'
        f'flex-shrink:0;margin-top:0.45rem;"></div>'
        f'<div style="font-size:0.875rem;color:#94A3B8;line-height:1.55;">{a}</div>'
        f'</div>'
        for a in areas
    ) or '<div style="color:#334155;font-size:0.85rem;">None recorded</div>'

    st.markdown(
        f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:14px;padding:1.1rem 1.25rem;margin-bottom:0.75rem;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#F59E0B;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.65rem;">'
        f'Areas to Improve</div>{a_items}</div>',
        unsafe_allow_html=True,
    )

    # Summary card
    st.markdown(
        f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:14px;padding:1.1rem 1.25rem;">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.65rem;">'
        f'AI Assessment</div>'
        f'<div style="font-size:0.875rem;color:#94A3B8;line-height:1.8;">{summary}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  AI recommendations panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_ai_recommendations(report: dict):
    topics = report.get("recommended_topics") or []
    rec    = report.get("hiring_recommendation") or "—"
    fg, bg = _REC_PALETTE.get(rec, ("#94A3B8", "rgba(148,163,184,0.1)"))

    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">'
        'AI Recommendations</div>',
        unsafe_allow_html=True,
    )

    # Hiring verdict card
    verdict_icons = {
        "Needs Improvement":    "🔴",
        "Ready for Internship": "🟡",
        "Entry-Level Ready":    "🔵",
        "Strong Candidate":     "🟢",
        "Senior Ready":         "🟣",
    }
    icon = verdict_icons.get(rec, "⚪")

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,rgba(13,27,46,0.95),rgba(7,16,41,0.98));
                    border:1px solid {fg}30;border-radius:16px;padding:1.4rem 1.5rem;
                    margin-bottom:0.75rem;position:relative;overflow:hidden;">
          <div style="position:absolute;top:0;left:0;right:0;height:2px;
                      background:linear-gradient(90deg,transparent,{fg},transparent);"></div>
          <div style="font-size:0.68rem;font-weight:700;color:#475569;
                      text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">
            Hiring Recommendation
          </div>
          <div style="display:flex;align-items:center;gap:0.75rem;">
            <div style="font-size:1.75rem;">{icon}</div>
            <div>
              <div style="font-size:1.05rem;font-weight:800;color:{fg};
                          letter-spacing:-0.02em;">{rec}</div>
              <div style="font-size:0.75rem;color:#64748B;margin-top:0.15rem;">
                Based on AI analysis of all answers
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Study topics card
    pills = "".join(
        f'<span style="display:inline-block;background:rgba(37,99,235,0.1);'
        f'border:1px solid rgba(37,99,235,0.2);color:#60A5FA;border-radius:100px;'
        f'padding:0.28rem 0.85rem;font-size:0.75rem;font-weight:500;'
        f'margin:0.2rem 0.15rem;">{t}</span>'
        for t in topics
    ) or '<span style="color:#334155;font-size:0.85rem;">No topics recorded</span>'

    st.markdown(
        f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:14px;padding:1.1rem 1.25rem;margin-bottom:0.75rem;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#64748B;'
        f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">'
        f'Recommended Study Topics</div>'
        f'<div style="line-height:2;">{pills}</div></div>',
        unsafe_allow_html=True,
    )

    # Next steps card
    next_steps = _derive_next_steps(report)
    steps_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:0.65rem;'
        f'padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.025);">'
        f'<div style="width:18px;height:18px;border-radius:50%;background:rgba(37,99,235,0.12);'
        f'border:1px solid rgba(37,99,235,0.2);display:flex;align-items:center;'
        f'justify-content:center;font-size:0.6rem;font-weight:700;color:#60A5FA;'
        f'flex-shrink:0;">{i+1}</div>'
        f'<div style="font-size:0.82rem;color:#94A3B8;line-height:1.55;">{step}</div>'
        f'</div>'
        for i, step in enumerate(next_steps)
    )

    st.markdown(
        f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
        f'border-radius:14px;padding:1.1rem 1.25rem;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#64748B;'
        f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.65rem;">'
        f'Suggested Next Steps</div>{steps_html}</div>',
        unsafe_allow_html=True,
    )


def _derive_next_steps(report: dict) -> List[str]:
    """Generate 3 contextual next steps from score data."""
    steps = []
    areas = report.get("improvement_areas") or []
    topics = report.get("recommended_topics") or []

    if areas:
        steps.append(f"Focus on: {areas[0]}")
    if topics:
        steps.append(f"Study {topics[0]} in depth before your next session")
    overall = report.get("overall_score") or 0
    if overall < 6:
        steps.append("Practice 2–3 more sessions at Beginner level to build confidence")
    elif overall < 8:
        steps.append("Attempt an Advanced difficulty session to push your limits")
    else:
        steps.append("You are ready — apply to roles and prepare for live interviews")
    return steps[:4]

# ─────────────────────────────────────────────────────────────────────────────
#  Interview timeline — Q&A drilldown
# ─────────────────────────────────────────────────────────────────────────────
def _render_timeline(answers: list):
    if not answers:
        return

    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">'
        'Question-by-Question Breakdown</div>',
        unsafe_allow_html=True,
    )

    for ans in answers:
        q_num    = ans.get("question_num", "?")
        q_text   = ans.get("question_text", "")
        a_text   = ans.get("answer_text", "")
        overall  = float(ans.get("overall", 0))
        feedback = ans.get("feedback", "")
        sc       = _sc(overall)

        label = f"Q{q_num}  ·  {overall}/10  ·  {q_text[:70]}{'…' if len(q_text)>70 else ''}"

        with st.expander(label):
            col_l, col_r = st.columns([3, 2], gap="large")

            with col_l:
                # Question
                st.markdown(
                    f'<div style="font-size:0.68rem;font-weight:700;color:#475569;'
                    f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.4rem;">'
                    f'Question</div>'
                    f'<div class="qa-q">{q_text}</div>',
                    unsafe_allow_html=True,
                )
                # Answer
                st.markdown(
                    f'<div style="font-size:0.68rem;font-weight:700;color:#475569;'
                    f'text-transform:uppercase;letter-spacing:0.12em;'
                    f'margin-top:0.75rem;margin-bottom:0.4rem;">Your Answer</div>'
                    f'<div class="qa-a">{a_text}</div>',
                    unsafe_allow_html=True,
                )
                # Feedback
                if feedback:
                    st.markdown(
                        f'<div style="font-size:0.68rem;font-weight:700;color:#475569;'
                        f'text-transform:uppercase;letter-spacing:0.12em;'
                        f'margin-top:0.75rem;margin-bottom:0.4rem;">AI Feedback</div>'
                        f'<div class="qa-fb">{feedback}</div>',
                        unsafe_allow_html=True,
                    )

            with col_r:
                # Score bars
                score_fields = [
                    ("Technical",       "technical"),
                    ("Communication",   "communication"),
                    ("Problem Solving", "problem_solving"),
                    ("Confidence",      "confidence"),
                    ("Completeness",    "completeness"),
                ]
                bars_html = ""
                for lbl, key in score_fields:
                    val = float(ans.get(key, 0))
                    pct = int(val * 10)
                    c   = _sc(val)
                    bars_html += (
                        f'<div class="mr-row">'
                        f'<span class="mr-lbl">{lbl}</span>'
                        f'<div class="mr-track"><div class="mr-fill" '
                        f'style="width:{pct}%;background:{c};"></div></div>'
                        f'<span class="mr-val" style="color:{c};">{val:.0f}</span>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div style="background:rgba(13,27,46,0.8);border:1px solid rgba(255,255,255,0.05);'
                    f'border-radius:12px;padding:1rem;">'
                    f'<div style="text-align:center;margin-bottom:0.85rem;">'
                    f'<div style="font-size:2rem;font-weight:900;color:{sc};'
                    f'letter-spacing:-0.04em;">{overall:.1f}</div>'
                    f'<div style="font-size:0.65rem;color:#475569;text-transform:uppercase;'
                    f'letter-spacing:0.1em;">Question Score</div>'
                    f'</div>{bars_html}</div>',
                    unsafe_allow_html=True,
                )

                # Per-answer strengths / improvements
                try:
                    strengths_list    = json.loads(ans.get("strengths") or "[]")
                    improvements_list = json.loads(ans.get("improvements") or "[]")
                except Exception:
                    strengths_list, improvements_list = [], []

                if strengths_list or improvements_list:
                    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                    sc1, sc2 = st.columns(2, gap="small")
                    with sc1:
                        if strengths_list:
                            items = "".join(
                                f'<div style="font-size:0.75rem;color:#86EFAC;'
                                f'padding:0.25rem 0;">✓ {x}</div>'
                                for x in strengths_list
                            )
                            st.markdown(
                                f'<div style="background:rgba(34,197,94,0.04);'
                                f'border:1px solid rgba(34,197,94,0.1);border-radius:8px;'
                                f'padding:0.6rem 0.75rem;">{items}</div>',
                                unsafe_allow_html=True,
                            )
                    with sc2:
                        if improvements_list:
                            items = "".join(
                                f'<div style="font-size:0.75rem;color:#FCD34D;'
                                f'padding:0.25rem 0;">→ {x}</div>'
                                for x in improvements_list
                            )
                            st.markdown(
                                f'<div style="background:rgba(245,158,11,0.04);'
                                f'border:1px solid rgba(245,158,11,0.1);border-radius:8px;'
                                f'padding:0.6rem 0.75rem;">{items}</div>',
                                unsafe_allow_html=True,
                            )
