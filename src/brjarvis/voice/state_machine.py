# voice/state_machine.py — Explicit Voice State Machine for BR JARVIS MK40.2
"""
Thread-safe explicit State Machine for the BR JARVIS Voice Assistant.

Defines all 16 formal voice states, transition validation rules, error
classifications, and bidirectional UI synchronization. Replaces unstructured
boolean flags with a verifiable state engine.
"""

from __future__ import annotations

import enum
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("JARVIS.Voice.StateMachine")


class VoiceState(str, enum.Enum):
    """Formal states of the BR JARVIS Voice Assistant."""

    IDLE = "IDLE"
    WAKE_DETECTION = "WAKE_DETECTION"
    WAKE_CONFIRMED = "WAKE_CONFIRMED"
    LISTENING_FOR_COMMAND = "LISTENING_FOR_COMMAND"
    CAPTURING = "CAPTURING"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    RESPONDING = "RESPONDING"
    SPEAKING = "SPEAKING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    WAITING_USER = "WAITING_USER"
    INTERRUPTED = "INTERRUPTED"
    CANCELLED = "CANCELLED"
    MUTED = "MUTED"
    RECOVERING = "RECOVERING"
    ERROR = "ERROR"


class VoiceErrorType(str, enum.Enum):
    """Categorized voice subsystem error types."""

    NONE = "NONE"
    MICROPHONE_UNAVAILABLE = "MICROPHONE_UNAVAILABLE"
    MICROPHONE_DISCONNECTED = "MICROPHONE_DISCONNECTED"
    WAKE_NOT_DETECTED = "WAKE_NOT_DETECTED"
    STT_TIMEOUT = "STT_TIMEOUT"
    STT_LOW_CONFIDENCE = "STT_LOW_CONFIDENCE"
    STT_PROVIDER_FAILURE = "STT_PROVIDER_FAILURE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_FAILURE = "LLM_FAILURE"
    TOOL_FAILURE = "TOOL_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    TTS_FAILURE = "TTS_FAILURE"
    BARGE_IN_FAILURE = "BARGE_IN_FAILURE"
    AUDIO_DEVICE_ERROR = "AUDIO_DEVICE_ERROR"


# Valid state transitions mapping: current_state -> set of allowed next states
VALID_TRANSITIONS: Dict[VoiceState, Set[VoiceState]] = {
    VoiceState.IDLE: {
        VoiceState.WAKE_DETECTION,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.MUTED,
        VoiceState.RECOVERING,
        VoiceState.ERROR,
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.PLANNING,
        VoiceState.SPEAKING,
    },
    VoiceState.WAKE_DETECTION: {
        VoiceState.WAKE_CONFIRMED,
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.IDLE,
        VoiceState.MUTED,
        VoiceState.RECOVERING,
        VoiceState.ERROR,
    },
    VoiceState.WAKE_CONFIRMED: {
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.UNDERSTANDING,
        VoiceState.WAKE_DETECTION,
        VoiceState.SPEAKING,
        VoiceState.IDLE,
        VoiceState.ERROR,
    },
    VoiceState.LISTENING_FOR_COMMAND: {
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.SPEAKING,
        VoiceState.MUTED,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.CAPTURING: {
        VoiceState.TRANSCRIBING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.TRANSCRIBING: {
        VoiceState.WAKE_CONFIRMED,
        VoiceState.UNDERSTANDING,
        VoiceState.PLANNING,
        VoiceState.EXECUTING,
        VoiceState.WAITING_USER,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.SPEAKING,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.UNDERSTANDING: {
        VoiceState.PLANNING,
        VoiceState.EXECUTING,
        VoiceState.WAITING_APPROVAL,
        VoiceState.WAITING_USER,
        VoiceState.RESPONDING,
        VoiceState.SPEAKING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.PLANNING: {
        VoiceState.EXECUTING,
        VoiceState.WAITING_APPROVAL,
        VoiceState.WAITING_USER,
        VoiceState.RESPONDING,
        VoiceState.SPEAKING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.WAKE_DETECTION,
        VoiceState.IDLE,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.EXECUTING: {
        VoiceState.RESPONDING,
        VoiceState.SPEAKING,
        VoiceState.WAITING_APPROVAL,
        VoiceState.WAITING_USER,
        VoiceState.PLANNING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.INTERRUPTED,
        VoiceState.CANCELLED,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.ERROR,
    },
    VoiceState.WAITING_APPROVAL: {
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.UNDERSTANDING,
        VoiceState.EXECUTING,
        VoiceState.CANCELLED,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.SPEAKING,
        VoiceState.ERROR,
    },
    VoiceState.WAITING_USER: {
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.UNDERSTANDING,
        VoiceState.EXECUTING,
        VoiceState.CANCELLED,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.SPEAKING,
        VoiceState.ERROR,
    },
    VoiceState.RESPONDING: {
        VoiceState.SPEAKING,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.ERROR,
    },
    VoiceState.SPEAKING: {
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.INTERRUPTED,
        VoiceState.CAPTURING,
        VoiceState.WAITING_USER,
        VoiceState.WAITING_APPROVAL,
        VoiceState.MUTED,
        VoiceState.ERROR,
    },
    VoiceState.INTERRUPTED: {
        VoiceState.LISTENING_FOR_COMMAND,
        VoiceState.CAPTURING,
        VoiceState.TRANSCRIBING,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.CANCELLED,
        VoiceState.ERROR,
    },
    VoiceState.CANCELLED: {
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.SPEAKING,
        VoiceState.ERROR,
    },
    VoiceState.MUTED: {
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.RECOVERING,
        VoiceState.ERROR,
    },
    VoiceState.RECOVERING: {
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.MUTED,
        VoiceState.ERROR,
    },
    VoiceState.ERROR: {
        VoiceState.RECOVERING,
        VoiceState.IDLE,
        VoiceState.WAKE_DETECTION,
        VoiceState.MUTED,
    },
}


class VoiceStateMachine:
    """
    Thread-safe State Machine for voice interactions.

    Provides state transitions, history auditing, listener hooks, error tracking,
    and automatic mapping to UI display states.
    """

    def __init__(self, initial_state: VoiceState = VoiceState.IDLE, ui_ref: Any = None):
        self._current_state = initial_state
        self._last_state = initial_state
        self._state_entered_time = time.monotonic()
        self._lock = threading.RLock()
        self._ui_ref = ui_ref
        self._listeners: List[Callable[[VoiceState, VoiceState, Dict[str, Any]], None]] = []
        self._last_error: VoiceErrorType = VoiceErrorType.NONE
        self._error_message: str = ""
        self._active_context: Dict[str, Any] = {}

    @property
    def current_state(self) -> VoiceState:
        with self._lock:
            return self._current_state

    @property
    def last_state(self) -> VoiceState:
        with self._lock:
            return self._last_state

    @property
    def state_duration_seconds(self) -> float:
        with self._lock:
            return time.monotonic() - self._state_entered_time

    @property
    def last_error(self) -> VoiceErrorType:
        with self._lock:
            return self._last_error

    @property
    def error_message(self) -> str:
        with self._lock:
            return self._error_message

    def add_listener(self, callback: Callable[[VoiceState, VoiceState, Dict[str, Any]], None]) -> None:
        """Register a state change listener callback(old_state, new_state, context)."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def transition_to(
        self, new_state: VoiceState, context: Optional[Dict[str, Any]] = None, force: bool = False
    ) -> bool:
        """
        Attempt transition to `new_state`.
        Returns True if transition succeeded, False if invalid and not forced.
        """
        with self._lock:
            old_state = self._current_state
            if old_state == new_state and not force:
                return True

            allowed = VALID_TRANSITIONS.get(old_state, set())
            if new_state not in allowed and not force:
                logger.warning(
                    "[VoiceStateMachine] Invalid transition rejected: %s -> %s", old_state.value, new_state.value
                )
                return False

            self._last_state = old_state
            self._current_state = new_state
            self._state_entered_time = time.monotonic()
            if context is not None:
                self._active_context.update(context)

            logger.info(
                "[VoiceStateMachine] Transition: %s -> %s (held %.2fs)",
                old_state.value,
                new_state.value,
                time.monotonic() - self._state_entered_time,
            )

            # Sync with UI if bound
            self._sync_ui(new_state)

            # Notify listeners
            listeners_copy = list(self._listeners)

        for listener in listeners_copy:
            try:
                listener(old_state, new_state, self._active_context)
            except Exception as e:
                logger.warning("[VoiceStateMachine] Listener error: %s", e)

        return True

    def set_error(self, error_type: VoiceErrorType, message: str = "") -> None:
        """Transition to ERROR state with classified error metadata."""
        with self._lock:
            self._last_error = error_type
            self._error_message = message
            logger.error("[VoiceStateMachine] Voice error: %s — %s", error_type.value, message)
        self.transition_to(VoiceState.ERROR, context={"error": error_type.value, "msg": message}, force=True)

    def clear_error(self) -> None:
        """Clear active error state."""
        with self._lock:
            self._last_error = VoiceErrorType.NONE
            self._error_message = ""

    def _sync_ui(self, state: VoiceState) -> None:
        """Map fine-grained voice state to UI state strings and sync with JarvisUI."""
        if not self._ui_ref:
            return

        ui_state_map = {
            VoiceState.IDLE: "IDLE",
            VoiceState.WAKE_DETECTION: "LISTENING",
            VoiceState.WAKE_CONFIRMED: "LISTENING",
            VoiceState.LISTENING_FOR_COMMAND: "LISTENING",
            VoiceState.CAPTURING: "LISTENING",
            VoiceState.TRANSCRIBING: "THINKING",
            VoiceState.UNDERSTANDING: "THINKING",
            VoiceState.PLANNING: "THINKING",
            VoiceState.EXECUTING: "EXECUTING",
            VoiceState.RESPONDING: "THINKING",
            VoiceState.SPEAKING: "SPEAKING",
            VoiceState.WAITING_APPROVAL: "WAITING_APPROVAL",
            VoiceState.WAITING_USER: "LISTENING",
            VoiceState.INTERRUPTED: "LISTENING",
            VoiceState.CANCELLED: "IDLE",
            VoiceState.MUTED: "IDLE",
            VoiceState.RECOVERING: "BUSY",
            VoiceState.ERROR: "ERROR",
        }

        mapped_ui_state = ui_state_map.get(state, "IDLE")

        try:
            if hasattr(self._ui_ref, "set_state"):
                self._ui_ref.set_state(mapped_ui_state)
            if hasattr(self._ui_ref, "speaking"):
                self._ui_ref.speaking = state == VoiceState.SPEAKING
        except Exception as e:
            logger.debug("[VoiceStateMachine] UI sync error: %s", e)
