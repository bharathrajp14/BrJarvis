"""Voice assistant interface and prompt refinement adapters."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("jarvis.surfaces.desktop.voice")

FILLER_PATTERNS = [
    r"\b(um+)\b",
    r"\b(uh+)\b",
    r"\b(ah+)\b",
    r"\b(er+)\b",
    r"\b(hmm+)\b",
]

PREFIX_BLOAT_PATTERNS = [
    r"^(hey\s+jarvis|ok\s+jarvis|hi\s+jarvis|hello\s+jarvis|jarvis)\b[\s,:\.\!]*",
    r"^(please\s+can\s+you|can\s+you\s+please|could\s+you\s+please|please|can\s+you)\b[\s,:\.\!]*",
]


@dataclass(slots=True)
class RefinedVoicePrompt:
    """Sanitized and normalized voice transcription ready for model dispatch."""

    raw_transcript: str
    cleaned_prompt: str
    is_empty: bool


def refine_voice_transcript(raw_text: str) -> RefinedVoicePrompt:
    """Clean acoustic speech transcript by removing filler sounds and wake-word prefixes."""
    text = raw_text.strip()
    if not text:
        return RefinedVoicePrompt(raw_transcript="", cleaned_prompt="", is_empty=True)

    cleaned = text
    prev = None
    while prev != cleaned:
        prev = cleaned
        for pat in FILLER_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        for pat in PREFIX_BLOAT_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return RefinedVoicePrompt(
        raw_transcript=raw_text,
        cleaned_prompt=cleaned or text,
        is_empty=len(cleaned) == 0,
    )
