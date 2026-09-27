# voice/__init__.py — JARVIS Voice Control Package
"""
Voice package re-exporting TTS, STT, and Assistant engines.

Imports are lazy so lightweight helpers such as ``prompt_refiner`` can be used
without pulling Qt, audio drivers, or the desktop HUD.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "NeuralTTS",
    "MCIPlayer",
    "SounddeviceMicrophone",
    "BRVoiceAssistant",
]


def __getattr__(name: str) -> Any:
    if name in {"NeuralTTS", "MCIPlayer"}:
        from .tts import MCIPlayer, NeuralTTS

        globals()["NeuralTTS"] = NeuralTTS
        globals()["MCIPlayer"] = MCIPlayer
        return globals()[name]
    if name == "SounddeviceMicrophone":
        from .stt import SounddeviceMicrophone

        globals()[name] = SounddeviceMicrophone
        return SounddeviceMicrophone
    if name == "BRVoiceAssistant":
        from .assistant import BRVoiceAssistant

        globals()[name] = BRVoiceAssistant
        return BRVoiceAssistant
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
