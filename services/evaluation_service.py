"""
Evaluation Service — scores candidate answers using the AI evaluator.

Key hardening:
- Prompt placeholders use named tokens (ROLE_PLACEHOLDER etc.) — no .format() on user content
- _validate_scores() fills all missing fields and clamps values
- Never crashes: all exceptions return a zero-score fallback with the error as feedback
- Type-safe score extraction (handles string digits from LLM)
"""

import logging
import os
from typing import Dict, Any, List

from services.ai_service import chat_completion_json, is_api_available

logger = logging.getLogger(__name__)

# Loaded once; never re-read on subsequent calls
_EVALUATOR_PROMPT: str = ""

# Required keys in every evaluation response
_SCORE_KEYS: List[str] = [
    "technical", "communication", "problem_solving", "confidence", "completeness"
]


def _load_prompt() -> str:
    """Load evaluator prompt template from disk (cached after first load)."""
    global _EVALUATOR_PROMPT
    if not _EVALUATOR_PROMPT:
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "evaluator_prompt.txt",
        )
        with open(path, "r", encoding="utf-8") as fh:
            _EVALUATOR_PROMPT = fh.read()
    return _EVALUATOR_PROMPT


def _build_system_prompt(role: str, difficulty: str, question: str, answer: str) -> str:
    """
    Substitute placeholders using simple string replacement.

    This avoids ALL .format() / f-string risks when user content contains
    curly braces (e.g. code snippets with dict literals).
    """
    template = _load_prompt()
    return (
        template
        .replace("ROLE_PLACEHOLDER", role)
        .replace("DIFFICULTY_PLACEHOLDER", difficulty)
        .replace("QUESTION_PLACEHOLDER", question)
        .replace("ANSWER_PLACEHOLDER", answer)
    )


def evaluate_answer(
    role: str,
    difficulty: str,
    question: str,
    answer: str,
) -> Dict[str, Any]:
    """
    Evaluate a candidate answer via LLM and return a validated score dict.

    Always returns a complete score dict — never raises.

    Schema:
        technical, communication, problem_solving, confidence, completeness: int 1-10
        overall: float (average)
        feedback: str
        strengths: list[str]
        improvements: list[str]
        key_topics_missed: list[str]
    """
    if not answer or len(answer.strip()) < 5:
        return _empty_scores("No answer provided.")

    if not is_api_available():
        return _empty_scores(
            "AI evaluation unavailable — GROQ_API_KEY not configured. "
            "Add your key to the .env file to enable scoring."
        )

    system_prompt = _build_system_prompt(role, difficulty, question, answer)

    try:
        raw_scores = chat_completion_json(
            system_prompt=system_prompt,
            user_message="Evaluate the answer and return only the JSON object.",
            temperature=0.2,
            max_tokens=800,
        )
        return _validate_scores(raw_scores)

    except Exception as exc:
        logger.error("Answer evaluation failed: %s", exc, exc_info=True)
        return _empty_scores(f"Evaluation unavailable: {str(exc)[:120]}")


def _validate_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise, clamp, and fill-in all score fields.

    Handles:
    - Missing keys (filled with default 5)
    - String values like "7" or "7.5" (converted to int/float)
    - Out-of-range values (clamped to 1-10)
    - Missing or non-list strengths/improvements
    """
    result: Dict[str, Any] = {}

    for key in _SCORE_KEYS:
        try:
            val = int(float(scores.get(key, 5)))  # handles "7", 7.9, etc.
        except (TypeError, ValueError):
            val = 5
        result[key] = max(1, min(10, val))

    # Recompute overall from the validated values (don't trust LLM's arithmetic)
    result["overall"] = round(
        sum(result[k] for k in _SCORE_KEYS) / len(_SCORE_KEYS), 1
    )

    result["feedback"] = str(scores.get("feedback") or "No feedback provided.")

    for list_key in ("strengths", "improvements", "key_topics_missed"):
        raw = scores.get(list_key)
        if isinstance(raw, list):
            result[list_key] = [str(item) for item in raw if item]
        else:
            result[list_key] = []

    return result


def _empty_scores(feedback: str) -> Dict[str, Any]:
    """Return a zero-score dict with a feedback message."""
    return {
        "technical": 0,
        "communication": 0,
        "problem_solving": 0,
        "confidence": 0,
        "completeness": 0,
        "overall": 0.0,
        "feedback": feedback,
        "strengths": [],
        "improvements": [],
        "key_topics_missed": [],
    }


def compute_final_report_scores(answers: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate per-answer scores into interview-level averages.

    Returns a dict with keys: overall_score, technical_avg, communication_avg,
    problem_solving_avg, confidence_avg, completeness_avg.
    """
    if not answers:
        return {
            "overall_score": 0.0,
            "technical_avg": 0.0,
            "communication_avg": 0.0,
            "problem_solving_avg": 0.0,
            "confidence_avg": 0.0,
            "completeness_avg": 0.0,
        }

    fields = ["technical", "communication", "problem_solving", "confidence", "completeness", "overall"]
    totals: Dict[str, float] = {f: 0.0 for f in fields}
    n = len(answers)

    for ans in answers:
        for f in fields:
            try:
                totals[f] += float(ans.get(f) or 0)
            except (TypeError, ValueError):
                pass

    return {
        "overall_score":        round(totals["overall"] / n, 1),
        "technical_avg":        round(totals["technical"] / n, 1),
        "communication_avg":    round(totals["communication"] / n, 1),
        "problem_solving_avg":  round(totals["problem_solving"] / n, 1),
        "confidence_avg":       round(totals["confidence"] / n, 1),
        "completeness_avg":     round(totals["completeness"] / n, 1),
    }
