"""Presentation surfaces for JARVIS (Web, CLI, Desktop)."""

from __future__ import annotations

from .cli import run_cli
from .desktop import RefinedVoicePrompt, refine_voice_transcript
from .web import create_app

__all__ = ["RefinedVoicePrompt", "create_app", "refine_voice_transcript", "run_cli"]
