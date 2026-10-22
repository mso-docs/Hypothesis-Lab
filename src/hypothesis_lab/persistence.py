"""Small local repository. SQLite belongs behind this boundary, not in the notebook."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/investigations.sqlite3")


def save(title: str, payload: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS investigations (title TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        db.execute(
            "INSERT OR REPLACE INTO investigations VALUES (?, ?)",
            (title, json.dumps(payload)),
        )


def load(title: str) -> dict | None:
    if not DB_PATH.exists():
        return None
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            "SELECT payload FROM investigations WHERE title = ?", (title,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def list_investigations() -> list[str]:
    """Return saved investigation names, newest writes first."""
    if not DB_PATH.exists():
        return []
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS investigations (title TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        return [
            row[0]
            for row in db.execute(
                "SELECT title FROM investigations ORDER BY rowid DESC"
            )
        ]
