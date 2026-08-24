"""Unit tests for Autonomous Task State Machine & Queue."""

from __future__ import annotations

import pytest

from brjarvis.agent.task_state import TaskStateManager, TaskStatus


@pytest.mark.unit
def test_task_state_transitions(tmp_path):
    """Verify task state transitions from PENDING -> RUNNING -> COMPLETED."""
    db_file = tmp_path / "test_tasks.db"
    mgr = TaskStateManager(db_path=db_file)

    task = mgr.create_task(goal="Analyze system memory consumption")
    assert task.status == TaskStatus.PENDING

    mgr.update_status(task.task_id, TaskStatus.RUNNING)
    assert mgr.get_task(task.task_id).status == TaskStatus.RUNNING

    mgr.update_status(task.task_id, TaskStatus.COMPLETED)
    completed = mgr.get_task(task.task_id)
    assert completed.status == TaskStatus.COMPLETED


@pytest.mark.unit
def test_stale_task_snapshot_is_rejected(tmp_path):
    """Concurrent managers must not silently overwrite a newer task revision."""
    from brjarvis.agent.task_state import ConcurrentTaskUpdateError

    db_file = tmp_path / "concurrent_tasks.db"
    first = TaskStateManager(db_path=db_file)
    second = TaskStateManager(db_path=db_file)
    task = first.create_task(goal="Preserve concurrent evidence")

    first_snapshot = first.get_task(task.task_id)
    second_snapshot = second.get_task(task.task_id)
    assert first_snapshot is not None
    assert second_snapshot is not None
    assert first_snapshot.revision == second_snapshot.revision == 0

    first_snapshot.current_step = 1
    first.save_task(first_snapshot)
    assert first_snapshot.revision == 1

    second_snapshot.current_step = 2
    with pytest.raises(ConcurrentTaskUpdateError):
        second.save_task(second_snapshot)

    persisted = first.get_task(task.task_id)
    assert persisted is not None
    assert persisted.current_step == 1
    assert persisted.revision == 1
