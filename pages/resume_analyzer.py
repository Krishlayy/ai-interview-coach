"""
Resume Analyzer — Upload a PDF resume and get an instant AI-powered assessment.
Score · ATS compatibility · Missing keywords · Strengths · Improvements
"""
import streamlit as st
import json
import logging
import os
from typing import Dict, Any

from services.resume_service import parse_resume, build_resume_context
from services.ai_service import chat_completion_json, is_api_available

logger = logging.getLogger(__name__)


# ─── Score-to-colour helper ──────────────────────────────────────────────────
def _sc(v: float) -> str:
    if v >= 80: return "#22C55E"
    if v >= 60: return "#3B82F6"
    if v >= 40: return "#F59E0B"
    return "#EF4444"


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def render():
    st.markdown(
        """
        <div style="margin-bottom:1.75rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#60A5FA;
                      text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.6rem;">
            Resume Analyzer
          </div>
          <div style="font-size:clamp(1.5rem,2.5vw,2.1rem);font-weight:900;
                      letter-spacing:-0.04em;
                      background:linear-gradient(135deg,#F8FAFC 0%,#94A3B8 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text;margin-bottom:0.4rem;">
            ATS &amp; Resume Score
          </div>
          <div style="font-size:0.9rem;color:#64748B;line-height:1.6;">
            Upload your PDF resume and get an instant score, ATS compatibility rating,
            missing keywords, and actionable improvement suggestions.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Session state
    if "ra_result" not in st.session_state:
        st.session_state.ra_result = None
    if "ra_parsed" not in st.session_state:
        st.session_state.ra_parsed = None

    col_up, col_res = st.columns([2, 3], gap="large")

    with col_up:
        _render_upload_panel()

    with col_res:
        if st.session_state.ra_result:
            _render_results(st.session_state.ra_result, st.session_state.ra_parsed)
        else:
            _render_placeholder()

# ─────────────────────────────────────────────────────────────────────────────
#  Upload panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_upload_panel():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:700;color:#64748B;'
        'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:1rem;">'
        'Upload Your Resume</div>',
        unsafe_allow_html=True,
    )

    resume_file = st.file_uploader(
        "Drop your PDF resume here",
        type=["pdf"],
        label_visibility="visible",
    )

    # Target role for keyword analysis
    target_role = st.selectbox(
        "Target Role",
        ["Software Engineer", "Python Developer", "Full Stack Developer",
         "AI Engineer", "Data Analyst"],
        help="Used to check for role-specific keywords",
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if resume_file:
        if st.button("Analyze Resume →", type="primary", use_container_width=True):
            with st.spinner("Parsing and scoring your resume…"):
                _run_analysis(resume_file.read(), target_role)
    else:
        st.markdown(
            '<div style="background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.12);'
            'border-radius:10px;padding:0.85rem 1rem;font-size:0.82rem;color:#475569;line-height:1.6;">'
            '📎 Upload a PDF to get your resume score, ATS compatibility, '
            'missing keywords, and improvement suggestions.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # What we check card
    st.markdown(
        """
        <div style="background:rgba(13,27,46,0.8);border:1px solid rgba(255,255,255,0.06);
                    border-radius:14px;padding:1.1rem 1.25rem;margin-top:0.75rem;">
          <div style="font-size:0.68rem;font-weight:700;color:#64748B;
                      text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.75rem;">
            What we analyse
          </div>
          <div style="display:flex;flex-direction:column;gap:0.5rem;">
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> Overall resume score
            </div>
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> ATS (applicant tracking) compatibility
            </div>
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> Missing high-value keywords
            </div>
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> Top technical strengths
            </div>
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> Actionable improvement suggestions
            </div>
            <div style="display:flex;gap:0.6rem;font-size:0.82rem;color:#94A3B8;">
              <span style="color:#22C55E;">✓</span> Skills gap vs target role
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  Placeholder (no result yet)
# ─────────────────────────────────────────────────────────────────────────────
def _render_placeholder():
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,rgba(13,27,46,0.92),rgba(7,16,41,0.96));
                    border:1px solid rgba(255,255,255,0.06);border-radius:24px;
                    padding:4rem 2rem;text-align:center;
                    box-shadow:0 8px 32px rgba(0,0,0,0.5);">
          <div style="width:72px;height:72px;border-radius:50%;margin:0 auto 1.5rem;
                      background:linear-gradient(135deg,rgba(37,99,235,0.12),rgba(124,58,237,0.12));
                      border:1px solid rgba(37,99,235,0.2);
                      display:flex;align-items:center;justify-content:center;font-size:2rem;">
            📄
          </div>
          <div style="font-size:1.2rem;font-weight:800;color:#F8FAFC;
                      letter-spacing:-0.03em;margin-bottom:0.6rem;">
            Your Analysis Will Appear Here
          </div>
          <div style="font-size:0.875rem;color:#64748B;max-width:340px;
                      margin:0 auto;line-height:1.65;">
            Upload your PDF resume and click <strong style="color:#94A3B8">Analyze Resume</strong>
            to see your score, ATS rating, missing keywords, and actionable suggestions.
          </div>
          <div style="display:flex;justify-content:center;gap:2rem;margin-top:2.5rem;flex-wrap:wrap;">
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:900;color:#3B82F6;">82</div>
              <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                          letter-spacing:0.1em;margin-top:0.2rem;">Resume Score</div>
            </div>
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:900;color:#22C55E;">91%</div>
              <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                          letter-spacing:0.1em;margin-top:0.2rem;">ATS Compatible</div>
            </div>
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:900;color:#F59E0B;">3</div>
              <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                          letter-spacing:0.1em;margin-top:0.2rem;">Missing Keywords</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Run AI analysis
# ─────────────────────────────────────────────────────────────────────────────
def _run_analysis(file_bytes: bytes, target_role: str):
    """Parse the resume then call the AI to score it. Stores result in session state."""
    parsed = parse_resume(file_bytes)
    if "error" in parsed:
        st.error(f"Could not parse PDF: {parsed['error']}")
        return

    st.session_state.ra_parsed = parsed

    if not is_api_available():
        # Offline fallback — heuristic scoring
        skills = parsed.get("skills", [])
        score  = min(95, max(30, len(skills) * 4 + 20))
        ats    = min(98, max(35, len(skills) * 3 + 30))
        result = _build_fallback_result(parsed, target_role, score, ats)
        st.session_state.ra_result = result
        return

    context = build_resume_context(parsed)
    system_prompt = (
        "You are a professional resume reviewer and ATS expert. "
        "Analyse the resume and return ONLY a valid JSON object — no markdown, no prose.\n\n"
        f"Target role: {target_role}\n\n"
        f"Resume content:\n{context[:3000]}\n\n"
        "Return exactly this structure:\n"
        "{\n"
        '  "resume_score": <integer 0-100>,\n'
        '  "ats_score": <integer 0-100>,\n'
        '  "missing_keywords": ["keyword1", "keyword2", "keyword3"],\n'
        '  "top_strengths": ["strength1", "strength2", "strength3"],\n'
        '  "improvement_suggestions": ["suggestion1", "suggestion2", "suggestion3"],\n'
        '  "skills_found": ["skill1", "skill2", "skill3"],\n'
        '  "verdict": "<one sentence overall verdict>"\n'
        "}"
    )

    try:
        result = chat_completion_json(
            system_prompt=system_prompt,
            user_message="Analyse this resume and return the JSON assessment.",
            temperature=0.2,
            max_tokens=700,
        )
        result = _validate_result(result, parsed, target_role)
    except Exception as exc:
        logger.error("Resume AI analysis failed: %s", exc)
        skills = parsed.get("skills", [])
        score  = min(95, max(30, len(skills) * 4 + 20))
        ats    = min(98, max(35, len(skills) * 3 + 30))
        result = _build_fallback_result(parsed, target_role, score, ats)

    st.session_state.ra_result = result
    st.rerun()


def _validate_result(result: dict, parsed: dict, role: str) -> dict:
    """Ensure all keys exist and values are sane."""
    result.setdefault("resume_score", 60)
    result.setdefault("ats_score", 65)
    result.setdefault("missing_keywords", [])
    result.setdefault("top_strengths", parsed.get("skills", [])[:3])
    result.setdefault("improvement_suggestions", ["Add quantified achievements"])
    result.setdefault("skills_found", parsed.get("skills", [])[:6])
    result.setdefault("verdict", "Resume analysed successfully.")
    result["resume_score"] = max(0, min(100, int(result["resume_score"])))
    result["ats_score"]    = max(0, min(100, int(result["ats_score"])))
    return result


def _build_fallback_result(parsed: dict, role: str, score: int, ats: int) -> dict:
    skills = parsed.get("skills", [])
    role_keywords = {
        "Software Engineer":    ["Docker", "AWS", "CI/CD", "System Design"],
        "Python Developer":     ["FastAPI", "Docker", "AWS", "PostgreSQL"],
        "Full Stack Developer": ["Docker", "AWS", "TypeScript", "Redis"],
        "AI Engineer":          ["PyTorch", "LangChain", "Docker", "MLflow"],
        "Data Analyst":         ["Tableau", "Power BI", "dbt", "Snowflake"],
    }
    wanted    = role_keywords.get(role, ["Docker", "AWS", "CI/CD"])
    missing   = [k for k in wanted if k.lower() not in [s.lower() for s in skills]][:3]
    strengths = skills[:3] if skills else ["Experience", "Education"]
    return {
        "resume_score": score,
        "ats_score": ats,
        "missing_keywords": missing,
        "top_strengths": strengths,
        "improvement_suggestions": [
            "Add quantified achievements (e.g. 'reduced load time by 40%')",
            "Add project impact metrics",
            "Improve the skills section with proficiency levels",
        ],
        "skills_found": skills[:8],
        "verdict": f"Heuristic analysis — AI scoring unavailable. Resume contains {len(skills)} detected skills.",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Results panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_results(result: dict, parsed: dict):
    rs  = result.get("resume_score", 0)
    ats = result.get("ats_score", 0)
    rs_c  = _sc(rs)
    ats_c = _sc(ats)

    # ── Score hero ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,rgba(13,27,46,0.95),rgba(7,16,41,0.98));
                    border:1px solid rgba(255,255,255,0.07);border-radius:20px;
                    padding:1.75rem 2rem;margin-bottom:1rem;position:relative;overflow:hidden;
                    box-shadow:0 8px 32px rgba(0,0,0,0.5);">
          <div style="position:absolute;top:0;left:0;right:0;height:2px;
                      background:linear-gradient(90deg,transparent,#2563EB 40%,#7C3AED 70%,transparent);">
          </div>
          <div style="display:flex;gap:2.5rem;flex-wrap:wrap;">
            <div style="text-align:center;min-width:90px;">
              <div style="font-size:2.8rem;font-weight:900;color:{rs_c};
                          letter-spacing:-0.04em;line-height:1;">{rs}</div>
              <div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
                          letter-spacing:0.1em;margin-top:0.2rem;">Resume Score</div>
              <div style="font-size:0.7rem;color:#475569;margin-top:0.1rem;">/ 100</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);flex-shrink:0;"></div>
            <div style="text-align:center;min-width:90px;">
              <div style="font-size:2.8rem;font-weight:900;color:{ats_c};
                          letter-spacing:-0.04em;line-height:1;">{ats}%</div>
              <div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
                          letter-spacing:0.1em;margin-top:0.2rem;">ATS Compatible</div>
              <div style="font-size:0.7rem;color:#475569;margin-top:0.1rem;">applicant tracking</div>
            </div>
            <div style="flex:1;display:flex;align-items:center;min-width:180px;">
              <div style="font-size:0.85rem;color:#94A3B8;line-height:1.65;font-style:italic;">
                "{result.get('verdict','')}"
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        # Missing keywords
        missing = result.get("missing_keywords") or []
        kw_html = "".join(
            f'<div style="display:flex;align-items:center;gap:0.55rem;'
            f'padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.03);">'
            f'<div style="width:6px;height:6px;border-radius:50%;'
            f'background:#EF4444;flex-shrink:0;"></div>'
            f'<span style="font-size:0.875rem;color:#CBD5E1;">{kw}</span>'
            f'</div>'
            for kw in missing
        ) or '<div style="font-size:0.85rem;color:#334155;">None detected — great work!</div>'

        st.markdown(
            f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(239,68,68,0.15);'
            f'border-radius:14px;padding:1.1rem 1.25rem;margin-bottom:0.75rem;">'
            f'<div style="font-size:0.68rem;font-weight:700;color:#EF4444;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.65rem;">'
            f'Missing Keywords</div>{kw_html}</div>',
            unsafe_allow_html=True,
        )

        # Improvement suggestions
        suggestions = result.get("improvement_suggestions") or []
        sg_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:0.55rem;'
            f'padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.03);">'
            f'<div style="width:6px;height:6px;border-radius:50%;'
            f'background:#F59E0B;flex-shrink:0;margin-top:0.45rem;"></div>'
            f'<span style="font-size:0.875rem;color:#94A3B8;line-height:1.55;">{sg}</span>'
            f'</div>'
            for sg in suggestions
        ) or '<div style="font-size:0.85rem;color:#334155;">No suggestions.</div>'

        st.markdown(
            f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(245,158,11,0.15);'
            f'border-radius:14px;padding:1.1rem 1.25rem;">'
            f'<div style="font-size:0.68rem;font-weight:700;color:#F59E0B;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.65rem;">'
            f'Improvement Suggestions</div>{sg_html}</div>',
            unsafe_allow_html=True,
        )

    with col_b:
        # Top strengths
        strengths = result.get("top_strengths") or []
        st_html = "".join(
            f'<div style="display:flex;align-items:center;gap:0.55rem;'
            f'padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.03);">'
            f'<div style="width:6px;height:6px;border-radius:50%;'
            f'background:#22C55E;flex-shrink:0;"></div>'
            f'<span style="font-size:0.875rem;color:#CBD5E1;">{s}</span>'
            f'</div>'
            for s in strengths
        ) or '<div style="font-size:0.85rem;color:#334155;">No strengths detected.</div>'

        st.markdown(
            f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(34,197,94,0.15);'
            f'border-radius:14px;padding:1.1rem 1.25rem;margin-bottom:0.75rem;">'
            f'<div style="font-size:0.68rem;font-weight:700;color:#22C55E;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.65rem;">'
            f'Top Strengths</div>{st_html}</div>',
            unsafe_allow_html=True,
        )

        # Detected skills
        skills_found = result.get("skills_found") or []
        pills = "".join(
            f'<span style="display:inline-block;background:rgba(37,99,235,0.1);'
            f'border:1px solid rgba(37,99,235,0.2);color:#60A5FA;border-radius:100px;'
            f'padding:0.22rem 0.8rem;font-size:0.75rem;font-weight:500;'
            f'margin:0.18rem 0.12rem;">{sk}</span>'
            for sk in skills_found
        ) or '<span style="font-size:0.85rem;color:#334155;">None detected.</span>'

        st.markdown(
            f'<div style="background:rgba(13,27,46,0.85);border:1px solid rgba(255,255,255,0.06);'
            f'border-radius:14px;padding:1.1rem 1.25rem;">'
            f'<div style="font-size:0.68rem;font-weight:700;color:#64748B;'
            f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.65rem;">'
            f'Detected Skills</div>'
            f'<div style="line-height:2.1;">{pills}</div></div>',
            unsafe_allow_html=True,
        )

    # Re-analyze button
    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        if st.button("Analyze Another Resume", use_container_width=True):
            st.session_state.ra_result = None
            st.session_state.ra_parsed = None
            st.rerun()
