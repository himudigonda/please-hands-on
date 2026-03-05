from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_task_roundtrip(tmp_path: Path) -> None:
    db_file = tmp_path / "test.db"
    os.environ["TASKPULSE_DB_PATH"] = str(db_file)

    app = create_app()
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["task_count"] >= 1

    before = client.get("/api/tasks")
    assert before.status_code == 200
    before_count = len(before.json())

    create = client.post("/api/tasks", json={"title": "write more tests"})
    assert create.status_code == 200
    created = create.json()
    assert created["title"] == "write more tests"
    assert created["completed"] is False

    toggled = client.patch(f"/api/tasks/{created['id']}")
    assert toggled.status_code == 200
    assert toggled.json()["completed"] is True

    after = client.get("/api/tasks")
    assert after.status_code == 200
    assert len(after.json()) == before_count + 1

    os.environ.pop("TASKPULSE_DB_PATH", None)
