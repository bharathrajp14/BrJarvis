"""Unit tests for Technical Vocabulary Prompt Refiner."""

from __future__ import annotations

import pytest

from brjarvis.voice.prompt_refiner import VoicePromptRefiner


@pytest.mark.unit
def test_prompt_refiner_vocabulary_normalization():
    """Verify common spoken tech terms are normalized to correct identifiers."""
    refiner = VoicePromptRefiner.get_instance()
    raw = "start fast api server with chroma db and open claw"
    refined_dict = refiner.refine(raw)

    refined = refined_dict["refined"]
    assert "FastAPI" in refined or "fastapi" in refined.lower()
    assert "ChromaDB" in refined or "chromadb" in refined.lower() or "chroma" in refined.lower()
    assert "OpenClaw" in refined or "openclaw" in refined.lower()


@pytest.mark.unit
def test_prompt_refiner_import_does_not_require_qt():
    """Voice transcript cleanup must not import the desktop HUD or Qt."""
    import importlib
    import sys

    sys.modules.pop("brjarvis.voice.assistant", None)
    sys.modules.pop("brjarvis.desktop.ui_mark", None)
    module = importlib.import_module("brjarvis.voice.prompt_refiner")
    assert "brjarvis.voice.assistant" not in sys.modules
    assert hasattr(module, "VoicePromptRefiner")


@pytest.mark.unit
def test_prompt_refiner_strip_fillers():
    """Verify hesitation fillers (um, uh, er) are removed."""
    refiner = VoicePromptRefiner.get_instance()
    raw = "um check uh the system status er please"
    cleaned = refiner.strip_fillers(raw)
    assert "um" not in cleaned.split()
    assert "uh" not in cleaned.split()
