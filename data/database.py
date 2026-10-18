"""
SQLite database interface for caching and persisting F1 session summaries,
favorite sessions, user annotations, and offline strategy runs.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(__file__), "storage")
DB_PATH = os.path.join(DB_DIR, "f1_cache.db")

def init_db():
    """Initializes the SQLite database tables."""
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_cache (
                session_key TEXT PRIMARY KEY,
                year INTEGER,
                event_name TEXT,
                session_type TEXT,
                circuit_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary_json TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT,
                lap_number INTEGER,
                driver TEXT,
                note_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT,
                driver TEXT,
                scenario_name TEXT,
                stops_count INTEGER,
                total_time_seconds REAL,
                stints_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_session_summary(session_key: str, year: int, event_name: str, session_type: str, circuit_name: str, summary: Dict[str, Any]):
    """Caches session summary in SQLite."""
    init_db()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO session_cache 
                (session_key, year, event_name, session_type, circuit_name, summary_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_key, year, event_name, session_type, circuit_name, json.dumps(summary, default=str)))
            conn.commit()
    except Exception as e:
        print(f"Error saving session summary to DB: {e}")

def get_session_summary(session_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves session summary from SQLite if available."""
    init_db()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT summary_json FROM session_cache WHERE session_key = ?", (session_key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
    except Exception:
        return None
    return None

def add_user_note(session_key: str, driver: str, lap_number: int, note_text: str):
    """Saves a user observation note."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_notes (session_key, driver, lap_number, note_text)
            VALUES (?, ?, ?, ?)
        """, (session_key, driver, lap_number, note_text))
        conn.commit()

def get_user_notes(session_key: str) -> List[Dict[str, Any]]:
    """Fetches user notes for a session."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, driver, lap_number, note_text, created_at FROM user_notes WHERE session_key = ? ORDER BY lap_number", (session_key,))
        rows = cursor.fetchall()
        return [{"id": r[0], "driver": r[1], "lap": r[2], "note": r[3], "timestamp": r[4]} for r in rows]
