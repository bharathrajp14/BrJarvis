"""Unit tests for BR JARVIS VoiceStateMachine lifecycle transitions."""
from __future__ import annotations

import pytest

from brjarvis.voice.state_machine import VoiceErrorType, VoiceState, VoiceStateMachine


@pytest.mark.unit
def test_wake_detection_to_transcribing_transition():
    """Verify that WAKE_DETECTION -> TRANSCRIBING transition is valid and allowed."""
    sm = VoiceStateMachine(initial_state=VoiceState.IDLE)
    assert sm.transition_to(VoiceState.WAKE_DETECTION) is True
    assert sm.current_state == VoiceState.WAKE_DETECTION

    # Transitioning to TRANSCRIBING must succeed (fixes user-reported bug)
    assert sm.transition_to(VoiceState.TRANSCRIBING) is True
    assert sm.current_state == VoiceState.TRANSCRIBING


@pytest.mark.unit
def test_voice_wake_detection_lifecycle_success():
    """Simulate full wake word detection lifecycle."""
    sm = VoiceStateMachine(initial_state=VoiceState.IDLE)

    # 1. Idle -> Wake Detection
    assert sm.transition_to(VoiceState.WAKE_DETECTION) is True

    # 2. Audio heard -> Transcribing wake audio
    assert sm.transition_to(VoiceState.TRANSCRIBING) is True

    # 3. Wake word recognized -> Wake Confirmed
    assert sm.transition_to(VoiceState.WAKE_CONFIRMED) is True

    # 4. Chime played -> Listening for command
    assert sm.transition_to(VoiceState.LISTENING_FOR_COMMAND) is True

    # 5. User spoken -> Transcribing command
    assert sm.transition_to(VoiceState.TRANSCRIBING) is True

    # 6. Command recognized -> Understanding
    assert sm.transition_to(VoiceState.UNDERSTANDING) is True

    # 7. Understanding -> Executing
    assert sm.transition_to(VoiceState.EXECUTING) is True

    # 8. Executing -> Speaking reply
    assert sm.transition_to(VoiceState.SPEAKING) is True

    # 9. Finished -> Back to Idle or Wake Detection
    assert sm.transition_to(VoiceState.IDLE) is True


@pytest.mark.unit
def test_voice_embedded_command_lifecycle():
    """Simulate wake phrase with embedded command (e.g. 'Hey Jarvis open chrome')."""
    sm = VoiceStateMachine(initial_state=VoiceState.WAKE_DETECTION)

    # Transcribe wake audio
    assert sm.transition_to(VoiceState.TRANSCRIBING) is True

    # Wake confirmed
    assert sm.transition_to(VoiceState.WAKE_CONFIRMED) is True

    # Embedded command directly moves to understanding
    assert sm.transition_to(VoiceState.UNDERSTANDING) is True

    # Understanding completed fast execution -> Idle
    assert sm.transition_to(VoiceState.IDLE) is True


@pytest.mark.unit
def test_voice_wake_phrase_not_detected_resumes():
    """Simulate noise heard during wake detection that does not match wake word."""
    sm = VoiceStateMachine(initial_state=VoiceState.WAKE_DETECTION)

    # Transcribe audio
    assert sm.transition_to(VoiceState.TRANSCRIBING) is True

    # Not a wake word -> Resume wake detection
    assert sm.transition_to(VoiceState.WAKE_DETECTION) is True
    assert sm.current_state == VoiceState.WAKE_DETECTION


@pytest.mark.unit
def test_voice_planning_initialization_transition():
    """Verify initialization transition from IDLE to PLANNING and then WAKE_DETECTION."""
    sm = VoiceStateMachine(initial_state=VoiceState.IDLE)

    assert sm.transition_to(VoiceState.PLANNING) is True
    assert sm.transition_to(VoiceState.WAKE_DETECTION) is True
    assert sm.current_state == VoiceState.WAKE_DETECTION
