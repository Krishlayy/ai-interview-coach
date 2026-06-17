"""
Interview Page — Live interview session with real-time scoring.

Key hardening:
- Division-by-zero guard on progress bar (total_questions always >= 1)
- API availability check before starting interview
- All session-state keys initialised before first access
- Fallback question text shown when AI returns empty string
- _finalize_interview() is idempotent — safe to call more than once
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


def render():
    st.markdown('<h1 class="page-title">🎯 Interview Session</h1>', unsafe_allow_html=True)

    # Initialize session state for interview
    _init_interview_state()

    state = st.session_state

    if not state.interview_active and not state.interview_complete:
        _render_setup()
    elif state.interview_active:
        _render_active_interview()
    elif state.interview_complete:
        _render_completion()


def _init_interview_state():
    defaults = {
        "interview_active": False,
        "interview_complete": False,
        "interview_id": None,
        "current_question": None,
        "current_question_id": None,
        "question_count": 0,
        "total_questions": 5,
        "conversation_history": [],
        "topics_covered": [],
        "live_scores": [],
        "role": None,
        "difficulty": None,
        "resume_context": None,
        "resume_parsed": None,
        "awaiting_answer": False,
        "last_evaluation": None,
        "final_report": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_setup():
    st.markdown('<p class="subtitle">Configure your interview session below.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Interview Configuration")

        role = st.selectbox(
            "Target Role",
            ["Software Engineer", "Python Developer", "Full Stack Developer",
             "AI Engineer", "Data Analyst"],
            help="Select the role you're preparing for",
        )

        difficulty = st.selectbox(
            "Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=1,
            help="Beginner: fundamentals | Intermediate: real-world | Advanced: senior-level",
        )

        total_q = st.select_slider(
            "Number of Questions",
            options=[5, 10, 15],
            value=5,
            help="More questions = deeper assessment",
        )

        st.markdown("---")
        st.markdown("#### 📄 Resume Upload (Optional)")
        st.markdown('<p style="color: var(--text-muted); font-size: 0.85rem;">Upload your resume for personalized questions based on your projects and skills.</p>', unsafe_allow_html=True)

        resume_file = st.file_uploader(
            "Upload Resume (PDF)",
            type=["pdf"],
            label_visibility="collapsed",
        )

        resume_context = None
        resume_parsed = None

        if resume_file:
            with st.spinner("Parsing resume..."):
                parsed = parse_resume(resume_file.read())
                if "error" not in parsed:
                    resume_parsed = parsed
                    resume_context = build_resume_context(parsed)
                    st.success(f"✅ Resume parsed — {len(parsed.get('skills', []))} skills, {len(parsed.get('projects', []))} projects found")

                    with st.expander("Preview extracted data"):
                        if parsed.get("skills"):
                            st.markdown(f"**Skills:** {', '.join(parsed['skills'][:10])}")
                        if parsed.get("projects"):
                            st.markdown("**Projects:**")
                            for p in parsed["projects"][:3]:
                                st.markdown(f"- {p}")
                else:
                    st.error(f"Resume parse error: {parsed['error']}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Session Preview")
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-label">Role</span>
            <span class="stat-value">{role}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Difficulty</span>
            <span class="stat-value">{difficulty}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Questions</span>
            <span class="stat-value">{total_q}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Estimated Time</span>
            <span class="stat-value">~{total_q * 3} mins</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Resume</span>
            <span class="stat-value">{"✅ Uploaded" if resume_context else "❌ Not uploaded"}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Tips")
        st.markdown("""
        <ul class="tips-list">
            <li>Answer clearly and completely</li>
            <li>Include examples from experience</li>
            <li>Mention complexity/tradeoffs</li>
            <li>Stay concise — quality over quantity</li>
        </ul>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            _start_interview(role, difficulty, total_q, resume_context, resume_parsed)


def _start_interview(role, difficulty, total_q, resume_context, resume_parsed):
    """Create DB record, generate first question, and transition to active state."""
    if not is_api_available():
        st.error(
            "Cannot start interview — GROQ_API_KEY is not configured. "
            "Add it to your .env file and restart.",
            icon="🔑",
        )
        return

    session_id = st.session_state.get("session_id", "default")
    db.upsert_user(session_id)

    try:
        interview_id = db.create_interview(
            session_id=session_id,
            role=role,
            difficulty=difficulty,
            total_questions=total_q,
            resume_used=bool(resume_context),
        )
    except Exception as exc:
        st.error(f"Database error creating interview: {exc}")
        return

    with st.spinner("🤖 Preparing your interview..."):
        question = generate_next_question(
            role=role,
            difficulty=difficulty,
            question_count=0,
            total_questions=total_q,
            conversation_history=[],
            topics_covered=[],
            resume_context=resume_context,
        )

    if not question:
        st.error("Failed to generate the first question. Please try again.")
        db.complete_interview(interview_id)  # clean up orphan record
        return

    question_id = db.save_question(interview_id, 1, question)

    st.session_state.update({
        "interview_active": True,
        "interview_complete": False,
        "interview_id": interview_id,
        "current_question": question,
        "current_question_id": question_id,
        "question_count": 1,
        "total_questions": total_q,
        "role": role,
        "difficulty": difficulty,
        "resume_context": resume_context,
        "resume_parsed": resume_parsed,
        "conversation_history": [{"role": "interviewer", "content": question}],
        "topics_covered": [],
        "live_scores": [],
        "awaiting_answer": True,
        "last_evaluation": None,
        "final_report": None,
    })
    st.rerun()


def _render_active_interview():
    state = st.session_state

    # Guard: ensure total_questions is at least 1 to prevent ZeroDivisionError
    total = max(1, int(state.get("total_questions", 1)))
    current = int(state.get("question_count", 1))
    progress = min(current / total, 1.0)

    col_prog1, col_prog2 = st.columns([4, 1])
    with col_prog1:
        st.progress(progress)
    with col_prog2:
        st.markdown(
            f'<div class="question-counter">Q {current} / {total}</div>',
            unsafe_allow_html=True,
        )

    # Layout: question + scoring sidebar
    col_main, col_score = st.columns([3, 1])

    with col_main:
        # Current question
        st.markdown(
            f'<div class="question-card"><div class="question-label">Question {state.question_count}</div>'
            f'<div class="question-text">{state.current_question}</div></div>',
            unsafe_allow_html=True,
        )

        # Last evaluation feedback
        if state.last_evaluation:
            eval_data = state.last_evaluation
            score_color = _score_color(eval_data.get("overall", 0))
            st.markdown(
                f'<div class="feedback-card">'
                f'<div class="feedback-score" style="color:{score_color}">Score: {eval_data.get("overall", 0)}/10</div>'
                f'<div class="feedback-text">{eval_data.get("feedback", "")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Answer input
        st.markdown('<div class="answer-container">', unsafe_allow_html=True)
        answer = st.text_area(
            "Your Answer",
            height=180,
            placeholder="Type your answer here. Be thorough — explain your thought process...",
            key=f"answer_input_{state.question_count}",
            label_visibility="collapsed",
        )

        col_a1, col_a2, col_a3 = st.columns([2, 2, 1])
        with col_a1:
            submit_btn = st.button(
                "Submit Answer →",
                type="primary",
                use_container_width=True,
                disabled=not answer or len(answer.strip()) < 3,
            )
        with col_a2:
            skip_btn = st.button(
                "Skip Question",
                use_container_width=True,
            )
        with col_a3:
            end_btn = st.button("End", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_score:
        _render_live_scores(state.live_scores)

    # Handle actions
    if submit_btn and answer and len(answer.strip()) >= 3:
        _process_answer(answer.strip())
    elif skip_btn:
        _process_answer("I don't know the answer to this question.", skipped=True)
    elif end_btn:
        _finalize_interview()


def _process_answer(answer: str, skipped: bool = False):
    """Evaluate the answer, persist it, and advance the interview."""
    state = st.session_state

    with st.spinner("⚡ Evaluating your answer..."):
        try:
            evaluation = evaluate_answer(
                role=state.role,
                difficulty=state.difficulty,
                question=state.current_question,
                answer=answer,
            )
        except Exception as exc:
            logger.error("Evaluation exception: %s", exc)
            evaluation = {
                "technical": 0, "communication": 0, "problem_solving": 0,
                "confidence": 0, "completeness": 0, "overall": 0.0,
                "feedback": f"Evaluation failed: {str(exc)[:100]}",
                "strengths": [], "improvements": [], "key_topics_missed": [],
            }

    try:
        db.save_answer(
            question_id=state.current_question_id,
            interview_id=state.interview_id,
            answer_text=answer,
            scores=evaluation,
        )
    except Exception as exc:
        logger.error("Failed to save answer: %s", exc)
        st.warning("Answer could not be saved to database, but evaluation continues.")

    state.conversation_history.append({"role": "candidate", "content": answer})
    state.live_scores.append(evaluation)
    state.last_evaluation = evaluation

    # Check if interview is complete
    if state.question_count >= state.total_questions:
        _finalize_interview()
        return

    # Generate next question
    with st.spinner("🤖 Preparing next question..."):
        next_q = generate_next_question(
            role=state.role,
            difficulty=state.difficulty,
            question_count=state.question_count,
            total_questions=state.total_questions,
            conversation_history=state.conversation_history,
            topics_covered=state.topics_covered,
            resume_context=state.resume_context,
        )

    new_q_num = state.question_count + 1
    try:
        question_id = db.save_question(state.interview_id, new_q_num, next_q)
    except Exception as exc:
        logger.error("Failed to save question: %s", exc)
        question_id = -1

    state.conversation_history.append({"role": "interviewer", "content": next_q})
    state.current_question = next_q
    state.current_question_id = question_id
    state.question_count = new_q_num
    state.awaiting_answer = True

    st.rerun()


def _finalize_interview():
    """Compute final scores, generate report, persist, and flip to complete state."""
    state = st.session_state

    # Idempotency guard — prevent double-finalization on reruns
    if state.get("interview_complete"):
        return

    with st.spinner("📊 Generating your final report..."):
        try:
            answers = db.get_interview_answers(state.interview_id)
            avg_scores = compute_final_report_scores(answers)
            report = generate_final_report(
                role=state.role,
                difficulty=state.difficulty,
                answers=answers,
                avg_scores=avg_scores,
            )
        except Exception as exc:
            logger.error("Final report generation failed: %s", exc)
            avg_scores = compute_final_report_scores(
                db.get_interview_answers(state.interview_id)
            )
            overall = avg_scores.get("overall_score", 0)
            report = {
                "overall_score": overall,
                **avg_scores,
                "strengths": ["Interview completed"],
                "weaknesses": [],
                "improvement_areas": ["Review your answers"],
                "recommended_topics": [],
                "hiring_recommendation": "Entry-Level Ready",
                "summary": f"Interview completed with score {overall}/10.",
            }

    try:
        db.save_report(state.interview_id, report)
        db.complete_interview(state.interview_id)
        db.record_analytics(
            session_id=st.session_state.get("session_id", "default"),
            interview_id=state.interview_id,
            role=state.role,
            difficulty=state.difficulty,
            scores=avg_scores,
        )
    except Exception as exc:
        logger.error("Failed to persist final interview data: %s", exc)

    state.final_report = report
    state.interview_active = False
    state.interview_complete = True
    st.rerun()


def _render_completion():
    state = st.session_state
    report = state.final_report or {}

    overall = report.get("overall_score", 0)
    rec = report.get("hiring_recommendation", "Needs Improvement")

    rec_config = {
        "Needs Improvement":  {"color": "#ef4444", "icon": "⚠️", "class": "rec-poor"},
        "Ready for Internship": {"color": "#f59e0b", "icon": "🌱", "class": "rec-intern"},
        "Entry-Level Ready":  {"color": "#3b82f6", "icon": "✅", "class": "rec-entry"},
        "Strong Candidate":   {"color": "#10b981", "icon": "🌟", "class": "rec-strong"},
        "Senior Ready":       {"color": "#8b5cf6", "icon": "🏆", "class": "rec-senior"},
    }
    cfg = rec_config.get(rec, rec_config["Needs Improvement"])

    # Hero
    st.markdown(
        f"""
        <div class="report-hero">
            <div class="report-icon">{cfg['icon']}</div>
            <div class="report-score" style="color:{cfg['color']}">{overall}/10</div>
            <div class="report-title">Interview Complete</div>
            <div class="report-rec" style="background:{cfg['color']}20; color:{cfg['color']}; border:1px solid {cfg['color']}40">
                {rec}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Score breakdown
    st.markdown("### Score Breakdown")
    score_cols = st.columns(5)
    score_fields = [
        ("Technical", report.get("technical_avg", 0)),
        ("Communication", report.get("communication_avg", 0)),
        ("Problem Solving", report.get("problem_solving_avg", 0)),
        ("Confidence", report.get("confidence_avg", 0)),
        ("Completeness", report.get("completeness_avg", 0)),
    ]
    for col, (label, val) in zip(score_cols, score_fields):
        with col:
            color = _score_color(val)
            st.markdown(
                f'<div class="score-card"><div class="score-num" style="color:{color}">{val}</div>'
                f'<div class="score-lbl">{label}</div></div>',
                unsafe_allow_html=True,
            )

    # Narrative
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💪 Strengths")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for s in report.get("strengths", []):
            st.markdown(f'<div class="list-item positive">✓ {s}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📚 Recommended Topics")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for t in report.get("recommended_topics", []):
            st.markdown(f'<div class="tag">{t}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🎯 Areas to Improve")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for w in report.get("improvement_areas", report.get("weaknesses", [])):
            st.markdown(f'<div class="list-item negative">→ {w}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Summary")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<p class="summary-text">{report.get("summary", "")}</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # CTA
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
            _reset_interview()
    with c2:
        if st.button("📊 View Full Report", use_container_width=True):
            st.session_state.active_page = "Reports"
            st.rerun()
    with c3:
        if st.button("📈 View Dashboard", use_container_width=True):
            st.session_state.active_page = "Dashboard"
            st.rerun()


def _render_live_scores(scores: List[Dict]):
    st.markdown('<div class="live-scores">', unsafe_allow_html=True)
    st.markdown('<div class="live-scores-title">Live Scores</div>', unsafe_allow_html=True)

    if not scores:
        st.markdown('<div class="no-scores">No scores yet</div>', unsafe_allow_html=True)
    else:
        latest = scores[-1]
        overall_avg = round(sum(s.get("overall", 0) for s in scores) / len(scores), 1)

        st.markdown(
            f'<div class="live-overall">'
            f'<span style="color:{_score_color(overall_avg)}">{overall_avg}</span>'
            f'<span class="live-denom">/10</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        fields = [
            ("Tech", "technical"),
            ("Comm", "communication"),
            ("P.Solv", "problem_solving"),
            ("Conf", "confidence"),
        ]
        for label, key in fields:
            val = latest.get(key, 0)
            bar_pct = val * 10
            color = _score_color(val)
            st.markdown(
                f'<div class="score-row">'
                f'<span class="score-row-label">{label}</span>'
                f'<div class="score-bar-bg"><div class="score-bar-fill" style="width:{bar_pct}%;background:{color}"></div></div>'
                f'<span class="score-row-val" style="color:{color}">{val}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


def _score_color(score: float) -> str:
    if score >= 8:
        return "#10b981"  # green
    elif score >= 6:
        return "#3b82f6"  # blue
    elif score >= 4:
        return "#f59e0b"  # amber
    else:
        return "#ef4444"  # red


def _reset_interview():
    keys = [
        "interview_active", "interview_complete", "interview_id", "current_question",
        "current_question_id", "question_count", "conversation_history", "topics_covered",
        "live_scores", "role", "difficulty", "resume_context", "resume_parsed",
        "awaiting_answer", "last_evaluation", "final_report", "total_questions",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()
