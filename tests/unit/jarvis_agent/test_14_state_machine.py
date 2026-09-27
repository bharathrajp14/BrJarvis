from __future__ import annotations

import pytest

from jarvis.agent import (
    InvalidStateTransitionError,
    TaskState,
    TaskStatus,
)


def test_14_canonical_states_exist() -> None:
    expected_states = [
        "CREATED",
        "QUEUED",
        "PLANNING",
        "WAITING_FOR_APPROVAL",
        "RUNNING",
        "WAITING_FOR_TOOL",
        "WAITING_FOR_USER",
        "VERIFYING",
        "RECOVERING",
        "PAUSED",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "ROLLED_BACK",
    ]
    for s in expected_states:
        assert hasattr(TaskStatus, s), f"Missing canonical state {s}"
        enum_val = getattr(TaskStatus, s)
        assert isinstance(enum_val, TaskStatus)


def test_state_aliases_and_case_insensitivity() -> None:
    # Lowercase lookup
    assert TaskStatus("created") == TaskStatus.CREATED
    # Uppercase lookup
    assert TaskStatus("QUEUED") == TaskStatus.QUEUED
    # Legacy alias lookup
    assert TaskStatus("waiting_approval") == TaskStatus.WAITING_FOR_APPROVAL
    assert TaskStatus.WAITING_APPROVAL == TaskStatus.WAITING_FOR_APPROVAL


def test_valid_state_transitions_and_event_trail() -> None:
    state = TaskState(task_id="task_state_test", user_request="Execute verified workflow")
    assert state.status == TaskStatus.CREATED
    assert len(state.events) == 0

    # CREATED -> QUEUED
    state.transition(TaskStatus.QUEUED, reason="Placed in job queue")
    assert state.status == TaskStatus.QUEUED
    assert len(state.events) == 1
    assert state.events[0]["from_status"] == "created"
    assert state.events[0]["to_status"] == "queued"
    assert state.events[0]["reason"] == "Placed in job queue"

    # QUEUED -> PLANNING
    state.transition(TaskStatus.PLANNING, reason="Decomposing user request")
    assert state.status == TaskStatus.PLANNING

    # PLANNING -> RUNNING
    state.transition(TaskStatus.RUNNING, reason="Dispatching first step")
    assert state.status == TaskStatus.RUNNING

    # RUNNING -> WAITING_FOR_TOOL
    state.transition(TaskStatus.WAITING_FOR_TOOL, reason="Waiting for browser automation")
    assert state.status == TaskStatus.WAITING_FOR_TOOL

    # WAITING_FOR_TOOL -> VERIFYING
    state.transition(TaskStatus.VERIFYING, reason="Validating DOM state")
    assert state.status == TaskStatus.VERIFYING

    # VERIFYING -> COMPLETED
    state.transition(TaskStatus.COMPLETED, reason="Verification criteria passed")
    assert state.status == TaskStatus.COMPLETED
    assert len(state.events) == 6


def test_invalid_state_transition_raises_error() -> None:
    state = TaskState(task_id="task_invalid_tx", user_request="Illegal transition test")
    assert state.status == TaskStatus.CREATED

    # Cannot jump directly from CREATED to COMPLETED
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        state.transition(TaskStatus.COMPLETED)
    assert "Invalid task state transition: created -> completed" in str(exc_info.value)

    # Force allows bypassing if needed for admin overrides
    state.transition(TaskStatus.COMPLETED, reason="Admin forced completion", force=True)
    assert state.status == TaskStatus.COMPLETED


def test_serialization_with_events() -> None:
    state = TaskState(task_id="t_ser", user_request="Serialization test")
    state.transition(TaskStatus.QUEUED, "Queued")
    state.transition(TaskStatus.PLANNING, "Planning")

    serialized = state.to_dict()
    assert serialized["status"] == "planning"
    assert len(serialized["events"]) == 2

    restored = TaskState.from_dict(serialized)
    assert restored.task_id == "t_ser"
    assert restored.status == TaskStatus.PLANNING
    assert len(restored.events) == 2
    assert restored.events[1]["to_status"] == "planning"
