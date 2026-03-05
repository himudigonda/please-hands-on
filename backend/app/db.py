from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    completed: bool
    created_at: str


def default_db_path() -> Path:
    configured = os.environ.get("TASKPULSE_DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "app.db"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def seed_if_empty(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    if count > 0:
        return

    seeds = [
        ("Ship benchmark harness", 0),
        ("Compare make/just/please", 0),
        ("Write instructions", 1),
    ]
    conn.executemany("INSERT INTO tasks(title, completed) VALUES(?, ?)", seeds)
    conn.commit()


def row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=int(row["id"]),
        title=str(row["title"]),
        completed=bool(row["completed"]),
        created_at=str(row["created_at"]),
    )


def list_tasks(conn: sqlite3.Connection) -> list[Task]:
    rows = conn.execute(
        "SELECT id, title, completed, created_at FROM tasks ORDER BY id DESC"
    ).fetchall()
    return [row_to_task(row) for row in rows]


def create_task(conn: sqlite3.Connection, title: str) -> Task:
    cursor = conn.execute(
        "INSERT INTO tasks(title, completed) VALUES(?, 0)", (title.strip(),)
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, title, completed, created_at FROM tasks WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return row_to_task(row)


def toggle_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute(
        "SELECT id, title, completed, created_at FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if row is None:
        return None

    new_value = 0 if int(row["completed"]) else 1
    conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_value, task_id))
    conn.commit()

    updated = conn.execute(
        "SELECT id, title, completed, created_at FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    return row_to_task(updated)


def health_payload(conn: sqlite3.Connection, db_path: Path) -> dict[str, Any]:
    count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    return {
        "status": "ok",
        "service": "taskpulse-backend",
        "database": str(db_path),
        "task_count": int(count),
    }
