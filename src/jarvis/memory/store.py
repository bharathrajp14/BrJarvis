"""Persistent repository for durable tasks and conversation sessions with optimistic concurrency control."""

from __future__ import annotations

import json
import time

from jarvis.agent.contracts import TaskStatus
from jarvis.agent.session import AgentSession
from jarvis.agent.task_state import TaskState

from .db import Database


class ConcurrencyError(Exception):
    """Raised when an update fails due to a revision mismatch."""


class TaskRepository:
    """Manages transactional task persistence with revision locking (DATA-001)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save_task(self, task: TaskState) -> None:
        """Persist a task state snapshot using atomic revision checking."""
        now = time.time()
        with self.db.write_transaction() as conn:
            # Check existence
            row = conn.execute("SELECT revision FROM tasks WHERE task_id = ?", (task.task_id,)).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO tasks (
                        task_id, user_request, status, current_step,
                        total_steps, revision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.task_id,
                        task.user_request,
                        task.status.value,
                        task.current_step,
                        task.total_steps,
                        task.revision,
                        task.created_at,
                        now,
                    ),
                )
            else:
                existing_rev = row["revision"]
                if existing_rev != task.revision:
                    raise ConcurrencyError(
                        f"Conflict saving task {task.task_id}: db has revision {existing_rev}, "
                        f"in-memory task has {task.revision}"
                    )

                new_rev = task.revision + 1
                cursor = conn.execute(
                    """
                    UPDATE tasks SET
                        user_request = ?,
                        status = ?,
                        current_step = ?,
                        total_steps = ?,
                        revision = ?,
                        updated_at = ?
                    WHERE task_id = ? AND revision = ?
                    """,
                    (
                        task.user_request,
                        task.status.value,
                        task.current_step,
                        task.total_steps,
                        new_rev,
                        now,
                        task.task_id,
                        task.revision,
                    ),
                )
                if cursor.rowcount == 0:
                    raise ConcurrencyError(f"Atomic update failed for task {task.task_id} (revision conflict)")
                task.revision = new_rev

            task.updated_at = now

    def get_task(self, task_id: str) -> TaskState | None:
        """Retrieve task by its ID."""
        with self.db.read_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None:
                return None

            return TaskState(
                task_id=row["task_id"],
                user_request=row["user_request"],
                status=TaskStatus(row["status"]),
                current_step=row["current_step"],
                total_steps=row["total_steps"],
                revision=row["revision"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_tasks(self, limit: int = 50) -> list[TaskState]:
        """List tasks ordered by updated timestamp descending."""
        with self.db.read_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                TaskState(
                    task_id=r["task_id"],
                    user_request=r["user_request"],
                    status=TaskStatus(r["status"]),
                    current_step=r["current_step"],
                    total_steps=r["total_steps"],
                    revision=r["revision"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]


class SessionRepository:
    """Manages persistent storage for interactive agent sessions and conversation messages."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save_session(self, session: AgentSession) -> None:
        """Persist session and its message history."""
        now = time.time()
        with self.db.write_transaction() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, correlation_id, current_mode, active_task_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    correlation_id = excluded.correlation_id,
                    current_mode = excluded.current_mode,
                    active_task_id = excluded.active_task_id,
                    updated_at = excluded.updated_at
                """,
                (
                    session.session_id,
                    session.correlation_id,
                    session.current_mode,
                    session.active_task_id,
                    session.created_at,
                    now,
                ),
            )

            # Persist turns
            for turn in session.history:
                conn.execute(
                    """
                    INSERT INTO messages (session_id, role, content, latency_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session.session_id,
                        turn.get("role", "unknown"),
                        turn.get("content", json.dumps(turn)),
                        turn.get("latency_ms", 0),
                        turn.get("timestamp", now),
                    ),
                )

    def get_session(self, session_id: str) -> AgentSession | None:
        """Hydrate session and its message history."""
        with self.db.read_connection() as conn:
            s_row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if s_row is None:
                return None

            m_rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
            ).fetchall()

            sess = AgentSession(
                session_id=s_row["session_id"],
                correlation_id=s_row["correlation_id"],
                current_mode=s_row["current_mode"],
                active_task_id=s_row["active_task_id"],
                created_at=s_row["created_at"],
            )
            for m in m_rows:
                sess.history.append({
                    "role": m["role"],
                    "content": m["content"],
                    "latency_ms": m["latency_ms"],
                    "timestamp": m["timestamp"],
                })
            return sess
