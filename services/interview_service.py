"""
Interview Service — question generation, conversation flow, and final report.

Key hardening:
- Prompt uses placeholder tokens (ROLE_PLACEHOLDER etc.) — no .format() on user content
- generate_final_report f-string JSON schema uses {{ }} for literal braces
- Every public function has a local fallback — never propagates exceptions to UI
- is_api_available() checked before calling Groq
"""

import logging
import os
from typing import List, Dict, Optional, Any

from services.ai_service import chat_completion, chat_completion_json, is_api_available

logger = logging.getLogger(__name__)

_INTERVIEWER_PROMPT: str = ""


def _load_interviewer_prompt() -> str:
    global _INTERVIEWER_PROMPT
    if not _INTERVIEWER_PROMPT:
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "interviewer_prompt.txt",
        )
        with open(path, "r", encoding="utf-8") as fh:
            _INTERVIEWER_PROMPT = fh.read()
    return _INTERVIEWER_PROMPT


def _build_interviewer_prompt(
    role: str,
    difficulty: str,
    question_count: int,
    total_questions: int,
    topics_covered: str,
    conversation_history: str,
) -> str:
    """
    Substitute all placeholders with simple string replacement.
    Safe against curly braces in user content.
    """
    template = _load_interviewer_prompt()
    return (
        template
        .replace("ROLE_PLACEHOLDER", role)
        .replace("DIFFICULTY_PLACEHOLDER", difficulty)
        .replace("QUESTION_COUNT_PLACEHOLDER", str(question_count))
        .replace("TOTAL_QUESTIONS_PLACEHOLDER", str(total_questions))
        .replace("TOPICS_COVERED_PLACEHOLDER", topics_covered)
        .replace("CONVERSATION_HISTORY_PLACEHOLDER", conversation_history)
    )


def generate_next_question(
    role: str,
    difficulty: str,
    question_count: int,
    total_questions: int,
    conversation_history: List[Dict[str, str]],
    topics_covered: List[str],
    resume_context: Optional[str] = None,
) -> str:
    """
    Generate the next interview question.

    Falls back to a hard-coded question bank if the API is unavailable or fails.
    Never raises.
    """
    if not is_api_available():
        logger.warning("API not available — using fallback question bank.")
        return _fallback_question(role, difficulty, question_count)

    history_text = _format_history(conversation_history)
    topics_text = ", ".join(topics_covered) if topics_covered else "None yet"

    system_prompt = _build_interviewer_prompt(
        role=role,
        difficulty=difficulty,
        question_count=question_count,
        total_questions=total_questions,
        topics_covered=topics_text,
        conversation_history=history_text,
    )

    if resume_context:
        system_prompt += (
            "\n\nResume context for personalised questions:\n"
            + resume_context[:1500]  # cap to avoid token overflow
        )

    user_msg = (
        "Start the interview with a brief professional greeting and ask the first question."
        if question_count == 0
        else f"Ask question number {question_count + 1} of {total_questions}."
    )

    try:
        question = chat_completion(
            system_prompt=system_prompt,
            user_message=user_msg,
            temperature=0.8,
            max_tokens=512,
        )
        return question.strip() or _fallback_question(role, difficulty, question_count)

    except Exception as exc:
        logger.error("Question generation failed: %s", exc, exc_info=True)
        return _fallback_question(role, difficulty, question_count)


def generate_final_report(
    role: str,
    difficulty: str,
    answers: List[Dict[str, Any]],
    avg_scores: Dict[str, float],
) -> Dict[str, Any]:
    """
    Generate a final interview report via LLM.

    Falls back to a rule-based report if the API is unavailable or fails.
    Never raises.
    """
    if not is_api_available():
        logger.warning("API not available — using fallback report.")
        return _fallback_report(avg_scores, avg_scores.get("overall_score", 0))

    answers_summary = _format_answers_for_report(answers)
    overall = avg_scores.get("overall_score", 0)

    # Use {{ }} for literal braces inside the f-string so they don't conflict
    system_prompt = (
        "You are a senior hiring manager generating a final interview assessment report.\n\n"
        f"Role: {role}\n"
        f"Difficulty: {difficulty}\n"
        f"Overall Score: {overall}/10\n\n"
        f"Answer Summary:\n{answers_summary}\n\n"
        "Score Breakdown:\n"
        f"- Technical: {avg_scores.get('technical_avg', 0)}/10\n"
        f"- Communication: {avg_scores.get('communication_avg', 0)}/10\n"
        f"- Problem Solving: {avg_scores.get('problem_solving_avg', 0)}/10\n"
        f"- Confidence: {avg_scores.get('confidence_avg', 0)}/10\n"
        f"- Completeness: {avg_scores.get('completeness_avg', 0)}/10\n\n"
        "Generate a comprehensive report. Return ONLY valid JSON with this exact structure:\n"
        '{{\n'
        '  "strengths": ["strength1", "strength2", "strength3"],\n'
        '  "weaknesses": ["weakness1", "weakness2"],\n'
        '  "improvement_areas": ["area1", "area2", "area3"],\n'
        '  "recommended_topics": ["topic1", "topic2", "topic3", "topic4"],\n'
        '  "hiring_recommendation": "one of: Needs Improvement | Ready for Internship | Entry-Level Ready | Strong Candidate | Senior Ready",\n'
        '  "summary": "3-4 sentence professional assessment paragraph"\n'
        '}}\n'
    )

    try:
        report = chat_completion_json(
            system_prompt=system_prompt,
            user_message="Generate the final interview report.",
            temperature=0.4,
            max_tokens=1200,
        )
        # Merge scores into report
        report.update(avg_scores)
        report["overall_score"] = overall
        # Validate hiring_recommendation value
        valid_recs = {
            "Needs Improvement", "Ready for Internship",
            "Entry-Level Ready", "Strong Candidate", "Senior Ready",
        }
        if report.get("hiring_recommendation") not in valid_recs:
            report["hiring_recommendation"] = _score_to_recommendation(overall)
        return report

    except Exception as exc:
        logger.error("Report generation failed: %s", exc, exc_info=True)
        return _fallback_report(avg_scores, overall)


# ─── Private helpers ───────────────────────────────────────────────────────────

def _format_history(conversation_history: List[Dict[str, str]]) -> str:
    if not conversation_history:
        return "No previous conversation."
    lines = []
    for turn in conversation_history[-8:]:  # last 8 turns
        role = turn.get("role", "unknown").capitalize()
        content = (turn.get("content") or "")[:400]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_answers_for_report(answers: List[Dict[str, Any]]) -> str:
    if not answers:
        return "No answers recorded."
    lines = []
    for i, ans in enumerate(answers, 1):
        q = (ans.get("question_text") or "")[:200]
        a = (ans.get("answer_text") or "")[:300]
        score = ans.get("overall", 0)
        lines.append(f"Q{i} (Score {score}/10): {q}\nAnswer: {a}\n")
    return "\n".join(lines)


def _score_to_recommendation(overall: float) -> str:
    if overall >= 8.5:
        return "Senior Ready"
    elif overall >= 7.0:
        return "Strong Candidate"
    elif overall >= 5.5:
        return "Entry-Level Ready"
    elif overall >= 4.0:
        return "Ready for Internship"
    return "Needs Improvement"


def _fallback_question(role: str, difficulty: str, count: int) -> str:
    """Return a role-appropriate fallback question when the API is unavailable."""
    banks: Dict[str, List[str]] = {
        "Software Engineer": [
            "Can you explain the difference between stack and heap memory?",
            "Walk me through how you would design a REST API for a user management system.",
            "What are the SOLID principles and how do you apply them in practice?",
            "Explain the CAP theorem and give a real-world example.",
            "How would you approach debugging a memory leak in a production service?",
        ],
        "Python Developer": [
            "Explain Python's GIL and its impact on multi-threading.",
            "What is the difference between generators and iterators in Python?",
            "How does Python manage memory and what is garbage collection?",
            "Describe how decorators work and give a practical use case.",
            "What are context managers and how do you implement one?",
        ],
        "Full Stack Developer": [
            "Explain the difference between client-side and server-side rendering.",
            "How would you optimize a slow database query?",
            "Describe your approach to handling authentication in a web application.",
            "What is the event loop in Node.js and how does it affect performance?",
            "How do you handle state management in a large React application?",
        ],
        "AI Engineer": [
            "Explain the transformer architecture and its key components.",
            "What is the difference between fine-tuning and RAG?",
            "How do you evaluate the performance of an LLM in production?",
            "What are embeddings and how are they used in semantic search?",
            "Describe the challenges of deploying LLMs at scale.",
        ],
        "Data Analyst": [
            "Explain the difference between GROUP BY and PARTITION BY in SQL.",
            "How would you handle missing data in a dataset?",
            "What metrics would you use to evaluate a classification model?",
            "Explain the difference between correlation and causation with an example.",
            "How do you approach exploratory data analysis on a new dataset?",
        ],
    }
    questions = banks.get(role, banks["Software Engineer"])
    return questions[count % len(questions)]


def _fallback_report(avg_scores: Dict[str, float], overall: float) -> Dict[str, Any]:
    rec = _score_to_recommendation(overall)
    report: Dict[str, Any] = {
        "strengths": ["Completed the interview", "Engaged with all questions"],
        "weaknesses": ["Detailed AI analysis unavailable"],
        "improvement_areas": ["Review core concepts for the role", "Practice more mock interviews"],
        "recommended_topics": ["Data Structures", "System Design", "Algorithms", "Communication Skills"],
        "hiring_recommendation": rec,
        "summary": (
            f"Candidate completed the interview with an overall score of {overall}/10. "
            f"The AI report generator was unavailable, so this is a rule-based assessment. "
            f"Based on the numeric scores, the recommendation is: {rec}. "
            "Please review individual question scores for detailed feedback."
        ),
    }
    report.update(avg_scores)
    report["overall_score"] = overall
    return report
