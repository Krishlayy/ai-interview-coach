"""
Database layer — SQLite with full schema for AI Interview Coach.
Handles all persistence: users, interviews, questions, answers, reports, analytics.

Singleton pattern: initialize_database() is safe to call multiple times —
it executes the schema only once per process lifetime.
"""

import sqlite3
import json
import logging
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "interview_coach.db")

# ─── Singleton guard — prevents repeated schema execution on Streamlit reruns ──
_DB_INITIALIZED: bool = False


def _get_db_path() -> str:
    """Ensure data directory exists and return DB path."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Thread-safe context manager for SQLite connections."""
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Database transaction failed: %s", exc, exc_info=True)
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """
    Create all tables and indexes if they don't exist.
    Uses a module-level flag so Streamlit reruns never re-execute the schema.
    """
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return

    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  TEXT    UNIQUE NOT NULL,
        name        TEXT    DEFAULT 'Candidate',
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS interviews (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id      TEXT    NOT NULL,
        role            TEXT    NOT NULL,
        difficulty      TEXT    NOT NULL,
        total_questions INTEGER NOT NULL,
        status          TEXT    DEFAULT 'in_progress',
        resume_used     INTEGER DEFAULT 0,
        started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at    DATETIME,
        FOREIGN KEY (session_id) REFERENCES users(session_id)
    );

    CREATE TABLE IF NOT EXISTS questions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id  INTEGER NOT NULL,
        question_num  INTEGER NOT NULL,
        question_text TEXT    NOT NULL,
        topic         TEXT    DEFAULT '',
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(id)
    );

    CREATE TABLE IF NOT EXISTS answers (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id     INTEGER NOT NULL,
        interview_id    INTEGER NOT NULL,
        answer_text     TEXT    NOT NULL,
        technical       REAL    DEFAULT 0,
        communication   REAL    DEFAULT 0,
        problem_solving REAL    DEFAULT 0,
        confidence      REAL    DEFAULT 0,
        completeness    REAL    DEFAULT 0,
        overall         REAL    DEFAULT 0,
        feedback        TEXT    DEFAULT '',
        strengths       TEXT    DEFAULT '[]',
        improvements    TEXT    DEFAULT '[]',
        topics_missed   TEXT    DEFAULT '[]',
        answered_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id)  REFERENCES questions(id),
        FOREIGN KEY (interview_id) REFERENCES interviews(id)
    );

    CREATE TABLE IF NOT EXISTS reports (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id          INTEGER UNIQUE NOT NULL,
        overall_score         REAL    DEFAULT 0,
        technical_avg         REAL    DEFAULT 0,
        communication_avg     REAL    DEFAULT 0,
        problem_solving_avg   REAL    DEFAULT 0,
        confidence_avg        REAL    DEFAULT 0,
        completeness_avg      REAL    DEFAULT 0,
        strengths             TEXT    DEFAULT '[]',
        weaknesses            TEXT    DEFAULT '[]',
        improvement_areas     TEXT    DEFAULT '[]',
        recommended_topics    TEXT    DEFAULT '[]',
        hiring_recommendation TEXT    DEFAULT '',
        summary               TEXT    DEFAULT '',
        generated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(id)
    );

    CREATE TABLE IF NOT EXISTS analytics (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id      TEXT    NOT NULL,
        interview_id    INTEGER NOT NULL,
        role            TEXT    NOT NULL,
        difficulty      TEXT    NOT NULL,
        overall_score   REAL    DEFAULT 0,
        technical       REAL    DEFAULT 0,
        communication   REAL    DEFAULT 0,
        problem_solving REAL    DEFAULT 0,
        confidence      REAL    DEFAULT 0,
        completeness    REAL    DEFAULT 0,
        recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id)   REFERENCES users(session_id),
        FOREIGN KEY (interview_id) REFERENCES interviews(id)
    );

    CREATE INDEX IF NOT EXISTS idx_interviews_session ON interviews(session_id);
    CREATE INDEX IF NOT EXISTS idx_answers_interview  ON answers(interview_id);
    CREATE INDEX IF NOT EXISTS idx_analytics_session  ON analytics(session_id);
    CREATE INDEX IF NOT EXISTS idx_analytics_role     ON analytics(role);
    """

    try:
        with get_connection() as conn:
            conn.executescript(schema)
        _DB_INITIALIZED = True
        logger.info("Database ready at: %s", _get_db_path())
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc, exc_info=True)
        raise


# ─── User helpers ──────────────────────────────────────────────────────────────

def upsert_user(session_id: str, name: str = "Candidate") -> None:
    """Insert or update user record."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (session_id, name) VALUES (?, ?)
            ON CONFLICT(session_id) DO UPDATE SET last_active = CURRENT_TIMESTAMP
            """,
            (session_id, name),
        )


# ─── Interview helpers ─────────────────────────────────────────────────────────

def create_interview(
    session_id: str,
    role: str,
    difficulty: str,
    total_questions: int,
    resume_used: bool = False,
) -> int:
    """Create a new interview record and return its ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO interviews (session_id, role, difficulty, total_questions, resume_used)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, difficulty, total_questions, int(resume_used)),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def complete_interview(interview_id: int) -> None:
    """Mark an interview as completed."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE interviews SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?",
            (interview_id,),
        )


def get_interview(interview_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM interviews WHERE id=?", (interview_id,)).fetchone()
        return dict(row) if row else None


def get_user_interviews(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Return completed interviews with joined report data."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT i.*, r.overall_score, r.hiring_recommendation
            FROM interviews i
            LEFT JOIN reports r ON r.interview_id = i.id
            WHERE i.session_id = ? AND i.status = 'completed'
            ORDER BY i.started_at DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Question helpers ──────────────────────────────────────────────────────────

def save_question(
    interview_id: int,
    question_num: int,
    question_text: str,
    topic: str = "",
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO questions (interview_id, question_num, question_text, topic) VALUES (?,?,?,?)",
            (interview_id, question_num, question_text, topic),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_interview_questions(interview_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM questions WHERE interview_id=? ORDER BY question_num",
            (interview_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Answer helpers ────────────────────────────────────────────────────────────

def save_answer(
    question_id: int,
    interview_id: int,
    answer_text: str,
    scores: Dict[str, Any],
) -> int:
    """Persist a scored answer."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO answers
              (question_id, interview_id, answer_text,
               technical, communication, problem_solving, confidence, completeness, overall,
               feedback, strengths, improvements, topics_missed)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                question_id,
                interview_id,
                answer_text,
                float(scores.get("technical", 0)),
                float(scores.get("communication", 0)),
                float(scores.get("problem_solving", 0)),
                float(scores.get("confidence", 0)),
                float(scores.get("completeness", 0)),
                float(scores.get("overall", 0)),
                scores.get("feedback", ""),
                json.dumps(scores.get("strengths", []) or []),
                json.dumps(scores.get("improvements", []) or []),
                json.dumps(scores.get("key_topics_missed", []) or []),
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_interview_answers(interview_id: int) -> List[Dict[str, Any]]:
    """Return all answers for an interview with their question text."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, q.question_text, q.question_num
            FROM answers a
            JOIN questions q ON q.id = a.question_id
            WHERE a.interview_id = ?
            ORDER BY q.question_num
            """,
            (interview_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Report helpers ────────────────────────────────────────────────────────────

def save_report(interview_id: int, report_data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR REPLACE INTO reports
              (interview_id, overall_score, technical_avg, communication_avg,
               problem_solving_avg, confidence_avg, completeness_avg,
               strengths, weaknesses, improvement_areas, recommended_topics,
               hiring_recommendation, summary)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                interview_id,
                float(report_data.get("overall_score") or 0),
                float(report_data.get("technical_avg") or 0),
                float(report_data.get("communication_avg") or 0),
                float(report_data.get("problem_solving_avg") or 0),
                float(report_data.get("confidence_avg") or 0),
                float(report_data.get("completeness_avg") or 0),
                json.dumps(report_data.get("strengths") or []),
                json.dumps(report_data.get("weaknesses") or []),
                json.dumps(report_data.get("improvement_areas") or []),
                json.dumps(report_data.get("recommended_topics") or []),
                report_data.get("hiring_recommendation") or "",
                report_data.get("summary") or "",
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_report(interview_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM reports WHERE interview_id=?", (interview_id,)
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        for field in ("strengths", "weaknesses", "improvement_areas", "recommended_topics"):
            try:
                data[field] = json.loads(data[field]) if data[field] else []
            except (json.JSONDecodeError, TypeError):
                data[field] = []
        return data


# ─── Analytics helpers ─────────────────────────────────────────────────────────

def record_analytics(
    session_id: str,
    interview_id: int,
    role: str,
    difficulty: str,
    scores: Dict[str, Any],
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analytics
              (session_id, interview_id, role, difficulty,
               overall_score, technical, communication, problem_solving, confidence, completeness)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id,
                interview_id,
                role,
                difficulty,
                float(scores.get("overall_score") or 0),
                float(scores.get("technical_avg") or 0),
                float(scores.get("communication_avg") or 0),
                float(scores.get("problem_solving_avg") or 0),
                float(scores.get("confidence_avg") or 0),
                float(scores.get("completeness_avg") or 0),
            ),
        )


def get_analytics(session_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, i.started_at
            FROM analytics a
            JOIN interviews i ON i.id = a.interview_id
            WHERE a.session_id = ?
            ORDER BY a.recorded_at ASC
            """,
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_dashboard_stats(session_id: str) -> Dict[str, Any]:
    """Return aggregate stats for the dashboard KPI cards."""
    with get_connection() as conn:
        stats_row = conn.execute(
            """
            SELECT
                COUNT(*)                       AS total_interviews,
                ROUND(AVG(overall_score), 1)   AS avg_score,
                ROUND(MAX(overall_score), 1)   AS best_score,
                ROUND(AVG(technical), 1)       AS avg_technical,
                ROUND(AVG(communication), 1)   AS avg_communication,
                ROUND(AVG(problem_solving), 1) AS avg_problem_solving,
                ROUND(AVG(confidence), 1)      AS avg_confidence
            FROM analytics
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

        result: Dict[str, Any] = dict(stats_row) if stats_row else {}

        # Determine weakest area safely
        area_map = {
            "Technical":       result.get("avg_technical") or 0,
            "Communication":   result.get("avg_communication") or 0,
            "Problem Solving": result.get("avg_problem_solving") or 0,
            "Confidence":      result.get("avg_confidence") or 0,
        }
        if any(v > 0 for v in area_map.values()):
            result["weakest_area"] = min(area_map, key=area_map.get)  # type: ignore[arg-type]
        else:
            result["weakest_area"] = "N/A"

        return result
