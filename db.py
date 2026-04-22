"""
db.py — SQLite database setup and helpers for the AI-powered forum.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "forum.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT    NOT NULL,
                body          TEXT    NOT NULL,
                tags          TEXT    NOT NULL DEFAULT '[]',
                embedding_json TEXT   NOT NULL DEFAULT '[]',
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


def insert_post(title: str, body: str, tags: list[str], embedding: list[float]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO posts (title, body, tags, embedding_json) VALUES (?, ?, ?, ?)",
            (title, body, json.dumps(tags), json.dumps(embedding)),
        )
        conn.commit()
        return cur.lastrowid


def fetch_all_posts() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, body, tags, embedding_json, created_at FROM posts ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def fetch_post(post_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, title, body, tags, embedding_json, created_at FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["tags"] = json.loads(d["tags"])
    d["embedding_json"] = json.loads(d["embedding_json"])
    return d
