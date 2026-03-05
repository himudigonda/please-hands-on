from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    task_count: int


def create_app() -> FastAPI:
    db_path = db.default_db_path()
    conn = db.connect(db_path)
    db.init_db(conn)
    db.seed_if_empty(conn)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        conn.close()

    app = FastAPI(title="TaskPulse API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> dict[str, str | int]:
        return db.health_payload(conn, db_path)

    @app.get("/api/tasks", response_model=list[TaskResponse])
    def get_tasks() -> list[db.Task]:
        return db.list_tasks(conn)

    @app.post("/api/tasks", response_model=TaskResponse)
    def post_task(payload: TaskCreate) -> db.Task:
        return db.create_task(conn, payload.title)

    @app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
    def patch_task(task_id: int) -> db.Task:
        updated = db.toggle_task(conn, task_id)
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated

    return app


app = create_app()
