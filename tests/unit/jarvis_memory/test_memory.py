from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.agent.contracts import TaskStatus
from jarvis.agent.session import AgentSession
from jarvis.agent.task_state import TaskState
from jarvis.memory import (
    ConcurrencyError,
    Database,
    SessionRepository,
    TaskRepository,
    TemporalEngine,
    initialize_database,
)


@pytest.fixture
def memory_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test_jarvis.db"
    db = Database(db_file)
    initialize_database(db)
    return db


def test_task_repository_atomic_revision_locking(memory_db: Database) -> None:
    repo = TaskRepository(memory_db)

    # 1. Insert new task
    task = TaskState(task_id="t_alpha", user_request="Initial task request")
    assert task.revision == 0
    repo.save_task(task)

    # 2. Verify retrieval
    loaded = repo.get_task("t_alpha")
    assert loaded is not None
    assert loaded.user_request == "Initial task request"
    assert loaded.revision == 0

    # 3. Successful update increments revision in db and in-memory
    task.advance_step({"action": "ran audit"})
    task.transition(TaskStatus.RUNNING)
    repo.save_task(task)
    assert task.revision == 1

    loaded_v1 = repo.get_task("t_alpha")
    assert loaded_v1 is not None
    assert loaded_v1.revision == 1
    assert loaded_v1.status == TaskStatus.RUNNING

    # 4. Attempt update with stale revision triggers ConcurrencyError
    stale_task = TaskState(
        task_id="t_alpha",
        user_request="Stale concurrent worker overwrite",
        revision=0,  # Outdated!
    )
    with pytest.raises(ConcurrencyError) as exc:
        repo.save_task(stale_task)
    assert "Conflict saving task t_alpha" in str(exc.value)


def test_session_repository_save_and_hydrate(memory_db: Database) -> None:
    repo = SessionRepository(memory_db)

    sess = AgentSession(session_id="s_100", current_mode="dev")
    sess.add_user_turn("What is the system uptime?")
    sess.add_assistant_turn("Uptime is 4 days.", latency_ms=120)

    repo.save_session(sess)

    hydrated = repo.get_session("s_100")
    assert hydrated is not None
    assert hydrated.session_id == "s_100"
    assert hydrated.current_mode == "dev"
    assert len(hydrated.history) == 2
    assert hydrated.history[0]["content"] == "What is the system uptime?"
    assert hydrated.history[1]["latency_ms"] == 120


def test_temporal_engine_truth_and_history(memory_db: Database) -> None:
    temporal = TemporalEngine(memory_db)

    # Record initial truth
    fact1 = temporal.record_fact(
        entity="server",
        attribute="status",
        value="BOOTING",
        confidence=0.9,
    )
    assert fact1.value == "BOOTING"

    truth1 = temporal.get_current_truth("server", "status")
    assert truth1 is not None
    assert truth1.value == "BOOTING"
    assert truth1.valid_to is None

    # Update truth
    fact2 = temporal.record_fact(
        entity="server",
        attribute="status",
        value="ONLINE",
        confidence=1.0,
    )
    assert fact2.value == "ONLINE"

    truth2 = temporal.get_current_truth("server", "status")
    assert truth2 is not None
    assert truth2.value == "ONLINE"

    # Verify history retains both records with closed interval for first
    history = temporal.get_history("server", "status")
    assert len(history) == 2
    assert history[0].value == "BOOTING"
    assert history[0].valid_to is not None
    assert history[1].value == "ONLINE"
    assert history[1].valid_to is None
