
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "assets" / "career_mentor.db"


def get_connection():
    """Create a SQLite database connection."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    """Initialize all database tables."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                full_name TEXT,
                profession TEXT,
                education TEXT,
                experience TEXT,
                skills TEXT,
                career_goal TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                input_data TEXT,
                result TEXT,
                created_at TEXT NOT NULL
            )
        """)

        connection.commit()


def save_profile(
    user_id,
    full_name="",
    profession="",
    education="",
    experience="",
    skills=None,
    career_goal=""
):
    """Save or update a user's career profile."""

    if not user_id or not user_id.strip():
        raise ValueError("User ID is required.")

    skills_json = json.dumps(skills or [])
    current_time = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO profiles (
                user_id, full_name, profession, education,
                experience, skills, career_goal, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                profession = excluded.profession,
                education = excluded.education,
                experience = excluded.experience,
                skills = excluded.skills,
                career_goal = excluded.career_goal,
                updated_at = excluded.updated_at
        """, (
            user_id,
            full_name,
            profession,
            education,
            experience,
            skills_json,
            career_goal,
            current_time,
            current_time
        ))

        connection.commit()


def get_profile(user_id):
    """Retrieve a user's saved profile."""

    with get_connection() as connection:

        row = connection.execute(
            "SELECT * FROM profiles WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    if row is None:
        return None

    profile = dict(row)
    profile["skills"] = json.loads(profile["skills"] or "[]")

    return profile


def save_analysis(user_id, analysis_type, input_data, result):
    """Save an AI analysis in history."""

    if not user_id or not analysis_type:
        raise ValueError("User ID and analysis type are required.")

    current_time = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        cursor = connection.execute("""
            INSERT INTO analysis_history (
                user_id, analysis_type, input_data, result, created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            analysis_type,
            json.dumps(input_data, ensure_ascii=False),
            result,
            current_time
        ))

        connection.commit()

        return cursor.lastrowid


def get_recent_analyses(user_id, limit=10):
    """Get recent analysis records for a user."""

    limit = max(1, min(int(limit), 100))

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT * FROM analysis_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

    return [
        {
            **dict(row),
            "input_data": json.loads(row["input_data"] or "{}")
        }
        for row in rows
    ]


def delete_analysis(analysis_id, user_id):
    """Delete one analysis belonging to a specific user."""

    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM analysis_history
            WHERE id = ? AND user_id = ?
        """, (analysis_id, user_id))

        connection.commit()

        return cursor.rowcount > 0


def clear_analysis_history(user_id):
    """Delete all analysis history belonging to a specific user."""

    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM analysis_history
            WHERE user_id = ?
        """, (user_id,))

        connection.commit()

        return cursor.rowcount