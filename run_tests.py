"""
Integration test suite — runs without pytest, no external deps beyond project code.
Execute: python run_tests.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

passed = 0
failed = 0


def check(label, condition, info=""):
    global passed, failed
    if condition:
        print(f"PASS  {label}")
        passed += 1
    else:
        print(f"FAIL  {label}  {info}")
        failed += 1


# ─── 1. Database singleton ────────────────────────────────────────────────────
from database import database as db
db.initialize_database()
db.initialize_database()
db.initialize_database()
check("DB singleton (3x init no-op)", db._DB_INITIALIZED)

# ─── 2. Full interview lifecycle ──────────────────────────────────────────────
db.upsert_user("demo")
db.upsert_user("demo")  # idempotent
iid = db.create_interview("demo", "AI Engineer", "Advanced", 3)
check("create_interview returns int", isinstance(iid, int))

qid1 = db.save_question(iid, 1, "Explain transformers.")
scores = {
    "technical": 8, "communication": 7, "problem_solving": 8,
    "confidence": 7, "completeness": 8, "overall": 7.6,
    "feedback": "Solid.", "strengths": ["depth"],
    "improvements": ["examples"], "key_topics_missed": [],
}
aid1 = db.save_answer(qid1, iid, "Transformers use self-attention.", scores)
qid2 = db.save_question(iid, 2, "What is RAG?")
aid2 = db.save_answer(qid2, iid, "Retrieval Augmented Generation.", scores)
check("2 Q&A pairs saved", aid1 > 0 and aid2 > 0)

# ─── 3. Aggregate scores ──────────────────────────────────────────────────────
answers = db.get_interview_answers(iid)
from services.evaluation_service import compute_final_report_scores
agg = compute_final_report_scores(answers)
check("compute_final_report_scores overall", agg["overall_score"] == 7.6)
check("compute_final_report_scores technical_avg", agg["technical_avg"] == 8.0)

# ─── 4. Prompt placeholder safety ────────────────────────────────────────────
tricky_answer = 'Use a dict like {"key": "value"} and list comprehensions {i: i*2 for i in range(10)}'
from services.evaluation_service import _build_system_prompt
prompt = _build_system_prompt("Python Developer", "Intermediate", "What is a dict?", tricky_answer)
check("Prompt: ROLE_PLACEHOLDER replaced", "ROLE_PLACEHOLDER" not in prompt)
check("Prompt: user curly braces preserved verbatim", '{"key"' in prompt)

# ─── 5. JSON extraction edge cases ───────────────────────────────────────────
from services.ai_service import _extract_json
import json

sample_json = {
    "technical": 7, "communication": 8, "problem_solving": 7,
    "confidence": 6, "completeness": 8, "overall": 7.2,
    "feedback": "Good.", "strengths": ["clear"],
    "improvements": ["depth"], "key_topics_missed": [],
}
raw_str = json.dumps(sample_json)

r1 = _extract_json(raw_str)
check("_extract_json: raw JSON", r1["technical"] == 7)

r2 = _extract_json("Here is the evaluation:\n```json\n" + raw_str + "\n```")
check("_extract_json: markdown fenced", r2["technical"] == 7)

r3 = _extract_json("Sure: " + raw_str + " Hope this helps!")
check("_extract_json: JSON embedded in prose", r3["technical"] == 7)

# trailing comma
raw_trailing = '{"technical": 7, "communication": 8,}'
try:
    r4 = _extract_json(raw_trailing)
    check("_extract_json: trailing comma stripped", r4["technical"] == 7)
except Exception as e:
    check("_extract_json: trailing comma stripped", False, str(e))

# ─── 6. _validate_scores clamping ────────────────────────────────────────────
from services.evaluation_service import _validate_scores
v = _validate_scores({
    "technical": "9",   # string -> int
    "communication": 11,  # above max -> 10
    "problem_solving": 0,  # below min -> 1
    "confidence": -5,   # below min -> 1
    "completeness": 7.9,  # float -> int 7
})
check("_validate_scores: string '9' -> int 9", v["technical"] == 9)
check("_validate_scores: 11 clamped to 10", v["communication"] == 10)
check("_validate_scores: 0 clamped to 1", v["problem_solving"] == 1)
check("_validate_scores: -5 clamped to 1", v["confidence"] == 1)
check("_validate_scores: 7.9 -> int 7", v["completeness"] == 7)
check("_validate_scores: overall is float", isinstance(v["overall"], float))

# ─── 7. Fallback report ───────────────────────────────────────────────────────
from services.interview_service import _fallback_report, _score_to_recommendation
check("_score_to_recommendation 9.0 -> Senior Ready", _score_to_recommendation(9.0) == "Senior Ready")
check("_score_to_recommendation 7.5 -> Strong Candidate", _score_to_recommendation(7.5) == "Strong Candidate")
check("_score_to_recommendation 6.0 -> Entry-Level Ready", _score_to_recommendation(6.0) == "Entry-Level Ready")
check("_score_to_recommendation 4.5 -> Ready for Internship", _score_to_recommendation(4.5) == "Ready for Internship")
check("_score_to_recommendation 3.0 -> Needs Improvement", _score_to_recommendation(3.0) == "Needs Improvement")

fallback = _fallback_report(agg, 7.6)
check("_fallback_report hiring_recommendation", fallback["hiring_recommendation"] == "Strong Candidate")
check("_fallback_report strengths is list", isinstance(fallback["strengths"], list))
check("_fallback_report overall_score present", fallback["overall_score"] == 7.6)

# ─── 8. Report round-trip ─────────────────────────────────────────────────────
report_data = {
    **agg,
    "strengths": ["clear"],
    "weaknesses": [],
    "improvement_areas": ["depth"],
    "recommended_topics": ["Transformers"],
    "hiring_recommendation": "Strong Candidate",
    "summary": "Great interview.",
}
db.save_report(iid, report_data)
rdata = db.get_report(iid)
check("get_report: not None", rdata is not None)
check("get_report: strengths is list", isinstance(rdata["strengths"], list))
check("get_report: hiring_recommendation", rdata["hiring_recommendation"] == "Strong Candidate")

# ─── 9. Dashboard stats ───────────────────────────────────────────────────────
db.complete_interview(iid)
db.record_analytics("demo", iid, "AI Engineer", "Advanced", agg)
stats = db.get_dashboard_stats("demo")
check("dashboard stats: total_interviews >= 1", stats["total_interviews"] >= 1)
check("dashboard stats: weakest_area is string", isinstance(stats["weakest_area"], str))
check("dashboard stats: avg_score is numeric", (stats.get("avg_score") or 0) >= 0)

# ─── 10. API availability check ──────────────────────────────────────────────
from services.ai_service import is_api_available, GROQ_API_KEY
print(f"\n  [API Key present: {bool(GROQ_API_KEY)}]")
check("is_api_available returns bool", isinstance(is_api_available(), bool))

# ─── 11. evaluate_answer with empty input ────────────────────────────────────
from services.evaluation_service import evaluate_answer
result_empty = evaluate_answer("Software Engineer", "Intermediate", "What is a stack?", "")
check("evaluate_answer empty input -> overall=0", result_empty["overall"] == 0.0)
check("evaluate_answer empty input -> feedback set", len(result_empty["feedback"]) > 0)

# ─── Cleanup ─────────────────────────────────────────────────────────────────
try:
    os.remove(os.path.join(os.path.dirname(__file__), "data", "interview_coach.db"))
except Exception:
    pass

# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Tests passed: {passed}")
print(f"  Tests failed: {failed}")
print(f"{'='*50}")
if failed > 0:
    sys.exit(1)
