"""
Interview Page — Premium AI recruiter interface (Phase 3)
Setup · Active session · Completion screen
"""
import streamlit as st
import json
import logging
from typing import List, Dict

from services.interview_service import generate_next_question, generate_final_report
from services.evaluation_service import evaluate_answer, compute_final_report_scores
from services.resume_service import parse_resume, build_resume_context
from services.ai_service import is_api_available
from database import database as db

logger = logging.getLogger(__name__)

# ─── colour helpers ──────────────────────────────────────────────────────────
def _sc(v: float) -> str:
    if v >= 8: return "#22C55E"
    if v >= 6: return "#3B82F6"
    if v >= 4: return "#F59E0B"
    return "#EF4444"

_REC_CFG = {
    "Needs Improvement":   {"c": "#EF4444", "i": "⚠️"},
    "Ready for Internship":{"c": "#F59E0B", "i": "🌱"},
    "Entry-Level Ready":   {"c": "#3B82F6", "i": "✅"},
    "Strong Candidate":    {"c": "#22C55E", "i": "🌟"},
    "Senior Ready":        {"c": "#A78BFA", "i": "🏆"},
}

# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def render():
    # Scoped styles for this page — injected once per render cycle
    st.markdown(
        """
        <style>
        /* Mobile responsiveness for interview layout */
        @media (max-width: 768px) {
            .question-panel { padding: 1.25rem 1.25rem; }
            .q-text { font-size: 0.95rem; }
            .ai-panel { padding: 1.25rem 1rem; }
        }
        /* Progress bar keyframe — defined here so it doesn't re-inject per-answer */
        @keyframes iv-bar-grow {
            from { width: 0%; }
        }
        .iv-prog-fill { animation: iv-bar-grow 0.7s cubic-bezier(0.4,0,0.2,1) forwards; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _init_state()
    s = st.session_state
    if not s.interview_active and not s.interview_complete:
        _render_setup()
    elif s.interview_active:
        _render_active()
    else:
        _render_completion()

# ─────────────────────────────────────────────────────────────────────────────
#  State initialisation
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "interview_active": False, "interview_complete": False,
        "interview_id": None, "current_question": None,
        "current_question_id": None, "question_count": 0,
        "total_questions": 5, "conversation_history": [],
        "topics_covered": [], "live_scores": [],
        "role": None, "difficulty": None,
        "resume_context": None, "resume_parsed": None,
        "awaiting_answer": False, "last_evaluation": None,
        "final_report": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  Setup page
# ─────────────────────────────────────────────────────────────────────────────
def _render_setup():
    # Page header
    st.markdown(
        """
        <div style="margin-bottom:1.75rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#60A5FA;
                      text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.6rem;">
            AI Interview Coach
          </div>
          <div style="font-size:clamp(1.5rem,2.5vw,2.1rem);font-weight:900;
                      letter-spacing:-0.04em;
                      background:linear-gradient(135deg,#F8FAFC 0%,#94A3B8 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text;margin-bottom:0.4rem;">
            Start a New Interview
          </div>
          <div style="font-size:0.9rem;color:#64748B;line-height:1.6;">
            Configure your session, optionally upload your resume, then let the AI recruiter begin.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_main, col_side = st.columns([3, 2], gap="large")

    # ── Left: configuration ──────────────────────────────────────────────────
    with col_main:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:700;color:#64748B;'
            'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:1.1rem;">'
            'Session Configuration</div>',
            unsafe_allow_html=True,
        )

        role = st.selectbox(
            "Target Role",
            ["Software Engineer", "Python Developer", "Full Stack Developer",
             "AI Engineer", "Data Analyst"],
            help="The role you are preparing to interview for",
        )
        difficulty = st.selectbox(
            "Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=1,
            help="Beginner: fundamentals · Intermediate: real-world · Advanced: senior-level",
        )
        total_q = st.select_slider(
            "Number of Questions",
            options=[5, 10, 15],
            value=5,
            help="More questions produce a more accurate assessment",
        )

        # Resume upload section
        st.markdown(
            '<div style="margin-top:1.25rem;padding-top:1.25rem;'
            'border-top:1px solid rgba(255,255,255,0.05);">'
            '<div style="font-size:0.75rem;font-weight:700;color:#64748B;'
            'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.6rem;">'
            'Resume Upload <span style="color:#334155;font-weight:500;'
            'text-transform:none;letter-spacing:0">(Optional)</span></div>'
            '<div style="font-size:0.8rem;color:#475569;margin-bottom:0.75rem;line-height:1.55;">'
            'Upload your PDF resume to receive personalized questions based on your actual projects and skills.'
            '</div></div>',
            unsafe_allow_html=True,
        )

        resume_file = st.file_uploader(
            "Resume PDF", type=["pdf"], label_visibility="collapsed"
        )

        resume_context, resume_parsed = None, None
        if resume_file:
            with st.spinner("Parsing resume…"):
                parsed = parse_resume(resume_file.read())
            if "error" not in parsed:
                resume_parsed = parsed
                resume_context = build_resume_context(parsed)
                n_skills   = len(parsed.get("skills", []))
                n_projects = len(parsed.get("projects", []))
                st.markdown(
                    f'<div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);'
                    f'border-radius:10px;padding:0.75rem 1rem;font-size:0.82rem;color:#86EFAC;margin-top:0.5rem;">'
                    f'✓ Resume parsed — <strong>{n_skills}</strong> skills · '
                    f'<strong>{n_projects}</strong> projects detected</div>',
                    unsafe_allow_html=True,
                )
                if n_skills:
                    with st.expander("Preview extracted skills & projects"):
                        st.markdown(
                            "**Skills:** " + ", ".join(parsed["skills"][:12])
                        )
                        if parsed.get("projects"):
                            st.markdown("**Projects:**")
                            for p in parsed["projects"][:3]:
                                st.markdown(f"- {p}")
            else:
                st.error(f"Resume parse failed: {parsed['error']}")

        st.markdown("</div>", unsafe_allow_html=True)   # glass-card

    # ── Right: preview + tips ────────────────────────────────────────────────
    with col_side:
        resume_status = "✓ Uploaded" if resume_context else "Not uploaded"
        resume_color  = "#22C55E"    if resume_context else "#475569"

        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom:1rem;">
              <div style="font-size:0.75rem;font-weight:700;color:#64748B;
                          text-transform:uppercase;letter-spacing:0.12em;margin-bottom:1rem;">
                Session Preview
              </div>

              <div style="display:flex;flex-direction:column;gap:0.6rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                  <span style="font-size:0.82rem;color:#64748B;">Role</span>
                  <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">{role}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                  <span style="font-size:0.82rem;color:#64748B;">Difficulty</span>
                  <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">{difficulty}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                  <span style="font-size:0.82rem;color:#64748B;">Questions</span>
                  <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">{total_q}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                  <span style="font-size:0.82rem;color:#64748B;">Est. Time</span>
                  <span style="font-size:0.82rem;font-weight:600;color:#F8FAFC;">~{total_q * 3} min</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.5rem 0;">
                  <span style="font-size:0.82rem;color:#64748B;">Resume</span>
                  <span style="font-size:0.82rem;font-weight:600;color:{resume_color};">{resume_status}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="glass-card">
              <div style="font-size:0.75rem;font-weight:700;color:#64748B;
                          text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.9rem;">
                Tips for a great score
              </div>
              <div style="display:flex;flex-direction:column;gap:0.55rem;">
                <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;line-height:1.5;">
                  <span style="color:#3B82F6;flex-shrink:0;">→</span>
                  Answer completely — mention edge cases
                </div>
                <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;line-height:1.5;">
                  <span style="color:#3B82F6;flex-shrink:0;">→</span>
                  Explain your reasoning, not just the answer
                </div>
                <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;line-height:1.5;">
                  <span style="color:#3B82F6;flex-shrink:0;">→</span>
                  Include time/space complexity where relevant
                </div>
                <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;line-height:1.5;">
                  <span style="color:#3B82F6;flex-shrink:0;">→</span>
                  Use real examples from your own experience
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.6, 1])
    with c2:
        if st.button("Begin Interview →", type="primary", use_container_width=True):
            _start_interview(role, difficulty, total_q, resume_context, resume_parsed)

# ─────────────────────────────────────────────────────────────────────────────
#  Start interview (unchanged logic, existing hardening kept)
# ─────────────────────────────────────────────────────────────────────────────
def _start_interview(role, difficulty, total_q, resume_context, resume_parsed):
    if not is_api_available():
        st.error(
            "GROQ_API_KEY is not configured — AI features disabled. "
            "Add it to your .env file and restart.",
            icon="🔑",
        )
        return

    session_id = st.session_state.get("session_id", "default")
    db.upsert_user(session_id)

    try:
        interview_id = db.create_interview(
            session_id=session_id, role=role, difficulty=difficulty,
            total_questions=total_q, resume_used=bool(resume_context),
        )
    except Exception as exc:
        st.error(f"Database error: {exc}")
        return

    with st.spinner("AI recruiter is preparing your first question…"):
        question = generate_next_question(
            role=role, difficulty=difficulty, question_count=0,
            total_questions=total_q, conversation_history=[],
            topics_covered=[], resume_context=resume_context,
        )

    if not question:
        st.error("Could not generate the first question. Please try again.")
        db.complete_interview(interview_id)
        return

    question_id = db.save_question(interview_id, 1, question)

    st.session_state.update({
        "interview_active": True, "interview_complete": False,
        "interview_id": interview_id, "current_question": question,
        "current_question_id": question_id, "question_count": 1,
        "total_questions": total_q, "role": role, "difficulty": difficulty,
        "resume_context": resume_context, "resume_parsed": resume_parsed,
        "conversation_history": [{"role": "interviewer", "content": question}],
        "topics_covered": [], "live_scores": [],
        "awaiting_answer": True, "last_evaluation": None, "final_report": None,
    })
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  Active interview — main layout
# ─────────────────────────────────────────────────────────────────────────────
def _render_active():
    s = st.session_state
    total   = max(1, int(s.get("total_questions", 1)))
    current = int(s.get("question_count", 1))
    pct     = min(current / total, 1.0)

    # ── Top progress bar + meta row ──────────────────────────────────────────
    pct_int = int(pct * 100)
    st.markdown(
        f"""
        <style>
        @keyframes bar-grow {{
            from {{ width: 0%; }}
            to   {{ width: {pct_int}%; }}
        }}
        .iv-prog-wrap {{
            background: rgba(255,255,255,0.04);
            border-radius: 100px; height: 4px;
            overflow: hidden; margin-bottom: 0.5rem;
        }}
        .iv-prog-fill {{
            height: 100%; border-radius: 100px;
            background: linear-gradient(90deg, #2563EB, #7C3AED);
            width: {pct_int}%;
            box-shadow: 0 0 10px rgba(37,99,235,0.5);
            animation: bar-grow 0.7s cubic-bezier(0.4,0,0.2,1) forwards;
        }}
        </style>
        <div style="display:flex;justify-content:space-between;
                    align-items:center;margin-bottom:0.35rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#60A5FA;
                      text-transform:uppercase;letter-spacing:0.14em;">
            Live Interview
          </div>
          <div style="font-size:0.78rem;color:#64748B;font-weight:600;">
            Question <span style="color:#F8FAFC;">{current}</span>
            <span style="color:#334155;"> / {total}</span>
          </div>
        </div>
        <div class="iv-prog-wrap"><div class="iv-prog-fill"></div></div>
        <div style="display:flex;justify-content:space-between;
                    margin-bottom:1.5rem;margin-top:0.25rem;">
          <div style="font-size:0.72rem;color:#334155;">
            {s.get('role','—')} · {s.get('difficulty','—')}
          </div>
          <div style="font-size:0.72rem;color:#334155;">{pct_int}% complete</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Three-column layout: question | answer | right panel ─────────────────
    col_q, col_right = st.columns([3, 1], gap="large")

    with col_q:
        _render_question_panel(s, current)
        _render_feedback_bubble(s)
        _render_answer_area(s, current)

    with col_right:
        _render_ai_avatar_panel(s)
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        _render_score_panel(s.live_scores)
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        _render_confidence_meter(s.live_scores)

# ─────────────────────────────────────────────────────────────────────────────
#  Question panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_question_panel(s, current: int):
    q_text = s.get("current_question") or ""
    st.markdown(
        f"""
        <div class="question-panel">
          <div class="q-eyebrow">
            Question {current} of {s.get('total_questions',5)}
          </div>
          <div class="q-text">{q_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Feedback bubble (shown after a previous answer is evaluated)
# ─────────────────────────────────────────────────────────────────────────────
def _render_feedback_bubble(s):
    ev = s.get("last_evaluation")
    if not ev or ev.get("overall", 0) == 0:
        return
    score = ev.get("overall", 0)
    color = _sc(score)
    fb    = ev.get("feedback", "")
    st.markdown(
        f"""
        <div class="fb-bubble">
          <div class="fb-score" style="color:{color};">
            Previous answer · {score}/10
          </div>
          <div class="fb-text">{fb}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Answer input area + action buttons
# ─────────────────────────────────────────────────────────────────────────────
def _render_answer_area(s, current: int):
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#475569;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.5rem;">'
        'Your Answer</div>',
        unsafe_allow_html=True,
    )

    answer = st.text_area(
        "answer",
        height=190,
        placeholder=(
            "Type your answer here. Explain your reasoning clearly — "
            "mention trade-offs, complexity, and real examples where possible…"
        ),
        key=f"ans_{current}",
        label_visibility="collapsed",
    )

    char_count = len(answer.strip()) if answer else 0
    char_color = "#22C55E" if char_count >= 80 else ("#F59E0B" if char_count >= 20 else "#475569")
    st.markdown(
        f'<div style="text-align:right;font-size:0.68rem;color:{char_color};'
        f'margin-top:-0.4rem;margin-bottom:0.75rem;">'
        f'{char_count} characters</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([5, 3, 2], gap="small")
    with c1:
        submit = st.button(
            "Submit Answer →",
            type="primary",
            use_container_width=True,
            disabled=(not answer or char_count < 3),
        )
    with c2:
        skip = st.button("Skip Question", use_container_width=True)
    with c3:
        end  = st.button("End Session", use_container_width=True)

    if submit and answer and char_count >= 3:
        _process_answer(answer.strip())
    elif skip:
        _process_answer("I don't know the answer to this question.", skipped=True)
    elif end:
        _finalize_interview()

# ─────────────────────────────────────────────────────────────────────────────
#  AI avatar panel (right column, top)
# ─────────────────────────────────────────────────────────────────────────────
def _render_ai_avatar_panel(s):
    role = s.get("role", "Interview Coach")
    st.markdown(
        f"""
        <div class="ai-panel">
          <div class="ai-avatar">🤖</div>
          <div class="ai-name">AI Recruiter</div>
          <div class="ai-role">{role} specialist</div>
          <div class="ai-online">
            <div class="ai-dot"></div>
            Live Session
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Score panel (right column, middle)
# ─────────────────────────────────────────────────────────────────────────────
def _render_score_panel(scores: List[Dict]):
    if not scores:
        st.markdown(
            '<div class="score-panel">'
            '<div style="text-align:center;padding:1.5rem 0;">'
            '<div style="font-size:0.75rem;color:#334155;">No scores yet</div>'
            '<div style="font-size:0.68rem;color:#1E293B;margin-top:0.3rem;">'
            'Submit your first answer</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        return

    latest = scores[-1]
    overall_avg = round(sum(x.get("overall", 0) for x in scores) / len(scores), 1)
    color = _sc(overall_avg)

    bars = [
        ("Tech",    "technical"),
        ("Comm",    "communication"),
        ("Solve",   "problem_solving"),
        ("Conf",    "confidence"),
    ]
    bars_html = ""
    for lbl, key in bars:
        val = latest.get(key, 0)
        pct = val * 10
        c   = _sc(val)
        bars_html += (
            f'<div class="sb-row">'
            f'<span class="sb-lbl">{lbl}</span>'
            f'<div class="sb-track"><div class="sb-fill" style="width:{pct}%;background:{c};"></div></div>'
            f'<span class="sb-val" style="color:{c};">{val}</span>'
            f'</div>'
        )

    st.markdown(
        f"""
        <div class="score-panel">
          <div class="score-big" style="color:{color};">{overall_avg}</div>
          <div class="score-big-lbl">Session avg · /10</div>
          {bars_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Confidence meter (right column, bottom)
# ─────────────────────────────────────────────────────────────────────────────
def _render_confidence_meter(scores: List[Dict]):
    """
    Derive a 'confidence' reading from the recent confidence sub-scores.
    Displayed as a radial-style percentage bar using pure CSS.
    """
    if not scores:
        return

    # Rolling average of confidence over last 3 answers
    recent = scores[-3:]
    conf_avg = round(sum(x.get("confidence", 0) for x in recent) / len(recent), 1)
    pct      = int(conf_avg * 10)
    color    = _sc(conf_avg)

    label = "Excellent" if conf_avg >= 8 else (
            "Good"      if conf_avg >= 6 else (
            "Fair"      if conf_avg >= 4 else "Low"))

    # Segmented confidence bar
    segments_html = ""
    for i in range(10):
        filled = i < int(conf_avg)
        seg_c  = color if filled else "rgba(255,255,255,0.04)"
        segments_html += (
            f'<div style="flex:1;height:6px;border-radius:2px;'
            f'background:{seg_c};transition:background 0.4s;"></div>'
        )

    st.markdown(
        f"""
        <div class="score-panel" style="padding:1.25rem 1.1rem;">
          <div style="font-size:0.65rem;font-weight:700;color:#475569;
                      text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.85rem;">
            Confidence Meter
          </div>
          <div style="display:flex;justify-content:space-between;
                      align-items:flex-end;margin-bottom:0.6rem;">
            <div style="font-size:1.6rem;font-weight:900;
                        color:{color};letter-spacing:-0.04em;line-height:1;">
              {pct}%
            </div>
            <div style="font-size:0.72rem;font-weight:600;color:{color};">
              {label}
            </div>
          </div>
          <div style="display:flex;gap:3px;margin-bottom:0.6rem;">
            {segments_html}
          </div>
          <div style="font-size:0.68rem;color:#334155;line-height:1.5;">
            Based on your last {len(recent)} answer{"s" if len(recent)!=1 else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  Process answer (evaluation + advance)
# ─────────────────────────────────────────────────────────────────────────────
def _process_answer(answer: str, skipped: bool = False):
    s = st.session_state

    with st.spinner("Evaluating your answer…"):
        try:
            evaluation = evaluate_answer(
                role=s.role, difficulty=s.difficulty,
                question=s.current_question, answer=answer,
            )
        except Exception as exc:
            logger.error("Evaluation error: %s", exc)
            evaluation = {
                "technical":0,"communication":0,"problem_solving":0,
                "confidence":0,"completeness":0,"overall":0.0,
                "feedback": f"Evaluation unavailable: {str(exc)[:80]}",
                "strengths":[],"improvements":[],"key_topics_missed":[],
            }

    try:
        db.save_answer(
            question_id=s.current_question_id,
            interview_id=s.interview_id,
            answer_text=answer, scores=evaluation,
        )
    except Exception as exc:
        logger.error("save_answer failed: %s", exc)

    s.conversation_history.append({"role": "candidate", "content": answer})
    s.live_scores.append(evaluation)
    s.last_evaluation = evaluation

    if s.question_count >= s.total_questions:
        _finalize_interview()
        return

    with st.spinner("AI recruiter is thinking of the next question…"):
        next_q = generate_next_question(
            role=s.role, difficulty=s.difficulty,
            question_count=s.question_count,
            total_questions=s.total_questions,
            conversation_history=s.conversation_history,
            topics_covered=s.topics_covered,
            resume_context=s.resume_context,
        )

    new_num = s.question_count + 1
    try:
        q_id = db.save_question(s.interview_id, new_num, next_q)
    except Exception as exc:
        logger.error("save_question failed: %s", exc)
        q_id = -1

    s.conversation_history.append({"role": "interviewer", "content": next_q})
    s.current_question    = next_q
    s.current_question_id = q_id
    s.question_count      = new_num
    s.awaiting_answer     = True
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Finalise interview
# ─────────────────────────────────────────────────────────────────────────────
def _finalize_interview():
    s = st.session_state
    if s.get("interview_complete"):
        return

    with st.spinner("Generating your final report…"):
        try:
            answers    = db.get_interview_answers(s.interview_id)
            avg_scores = compute_final_report_scores(answers)
            report     = generate_final_report(
                role=s.role, difficulty=s.difficulty,
                answers=answers, avg_scores=avg_scores,
            )
        except Exception as exc:
            logger.error("Final report error: %s", exc)
            answers    = db.get_interview_answers(s.interview_id)
            avg_scores = compute_final_report_scores(answers)
            overall    = avg_scores.get("overall_score", 0)
            report     = {
                "overall_score": overall, **avg_scores,
                "strengths":["Interview completed"],"weaknesses":[],
                "improvement_areas":["Review your answers"],
                "recommended_topics":[],"hiring_recommendation":"Entry-Level Ready",
                "summary":f"Interview completed with score {overall}/10.",
            }

    try:
        db.save_report(s.interview_id, report)
        db.complete_interview(s.interview_id)
        db.record_analytics(
            session_id=st.session_state.get("session_id","default"),
            interview_id=s.interview_id, role=s.role, difficulty=s.difficulty,
            scores=avg_scores,
        )
    except Exception as exc:
        logger.error("Persist final data failed: %s", exc)

    s.final_report      = report
    s.interview_active  = False
    s.interview_complete= True
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  Completion / result screen
# ─────────────────────────────────────────────────────────────────────────────
def _render_completion():
    s      = st.session_state
    report = s.final_report or {}
    overall= report.get("overall_score", 0)
    rec    = report.get("hiring_recommendation", "Needs Improvement")
    cfg    = _REC_CFG.get(rec, _REC_CFG["Needs Improvement"])
    color  = cfg["c"]
    icon   = cfg["i"]

    # Hero banner
    st.markdown(
        f"""
        <div class="result-hero">
          <span class="rh-icon">{icon}</span>
          <div class="rh-score" style="color:{color};">{overall}/10</div>
          <div class="rh-lbl">Interview Complete</div>
          <div class="rh-badge" style="color:{color};border-color:{color}40;
                                       background:{color}18;">{rec}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Score cards row
    fields = [
        ("Technical",       report.get("technical_avg", 0)),
        ("Communication",   report.get("communication_avg", 0)),
        ("Problem Solving", report.get("problem_solving_avg", 0)),
        ("Confidence",      report.get("confidence_avg", 0)),
        ("Completeness",    report.get("completeness_avg", 0)),
    ]
    cols = st.columns(5, gap="small")
    for col, (lbl, val) in zip(cols, fields):
        with col:
            c = _sc(val or 0)
            st.markdown(
                f'<div class="score-card">'
                f'<div class="sc-num" style="color:{c};">{val or 0}</div>'
                f'<div class="sc-lbl">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")

    with col1:
        # Strengths
        strengths = report.get("strengths") or []
        items_html = "".join(
            f'<div class="list-item positive">'
            f'<div class="li-dot"></div>{s_}</div>'
            for s_ in strengths
        )
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.6rem;">'
            f'Strengths</div>'
            f'<div class="insight-card">{items_html or "<div style=color:#334155>None recorded</div>"}</div>',
            unsafe_allow_html=True,
        )

        # Recommended topics
        topics = report.get("recommended_topics") or []
        pills  = "".join(f'<span class="topic-pill">{t}</span>' for t in topics)
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
            f'text-transform:uppercase;letter-spacing:0.12em;'
            f'margin-top:1rem;margin-bottom:0.6rem;">Study Topics</div>'
            f'<div class="insight-card">{pills or "<div style=color:#334155>None recorded</div>"}</div>',
            unsafe_allow_html=True,
        )

    with col2:
        # Improvement areas
        areas  = report.get("improvement_areas") or report.get("weaknesses") or []
        items2 = "".join(
            f'<div class="list-item negative">'
            f'<div class="li-dot"></div>{a}</div>'
            for a in areas
        )
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.6rem;">'
            f'Areas to Improve</div>'
            f'<div class="insight-card">{items2 or "<div style=color:#334155>None recorded</div>"}</div>',
            unsafe_allow_html=True,
        )

        # Summary
        summary = report.get("summary", "")
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
            f'text-transform:uppercase;letter-spacing:0.12em;'
            f'margin-top:1rem;margin-bottom:0.6rem;">Assessment</div>'
            f'<div class="insight-card"><div class="summary-block">{summary}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if st.button("Start New Interview", type="primary", use_container_width=True):
            _reset_interview()
    with c2:
        if st.button("View Full Report", use_container_width=True):
            st.session_state.active_page = "Reports"
            st.rerun()
    with c3:
        if st.button("Go to Dashboard", use_container_width=True):
            st.session_state.active_page = "Dashboard"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Reset helper
# ─────────────────────────────────────────────────────────────────────────────
def _reset_interview():
    for k in [
        "interview_active","interview_complete","interview_id","current_question",
        "current_question_id","question_count","conversation_history","topics_covered",
        "live_scores","role","difficulty","resume_context","resume_parsed",
        "awaiting_answer","last_evaluation","final_report","total_questions",
    ]:
        st.session_state.pop(k, None)
    st.rerun()
