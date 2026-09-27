# voice/shortcuts.py — Voice Pattern Recognizer (Pure Matcher, No Execution)
"""
Voice Pattern Recognizer for acoustic phrase classification.
Zero execution capabilities — all execution is routed through the canonical pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger("JARVIS.VoiceShortcuts")


class VoiceShortcutRegistry:
    """Acoustic vocabulary pattern matcher for voice intent recognition."""

    def __init__(self):
        self._shortcuts: Dict[str, Tuple[re.Pattern, str, Dict]] = {}
        self._register_default_shortcuts()

    def register(self, key: str, pattern: str, intent_name: str, args: dict):
        self._shortcuts[key] = (re.compile(pattern, re.IGNORECASE), intent_name, args)

    def _register_default_shortcuts(self):
        self.register("stop_speech", r"^(stop speaking|be quiet|shut up|silence|stop talking)$", "stop_speech", {})
        self.register(
            "system_health",
            r"^(system health|system status|check system|computer status)$",
            "system_diagnostic",
            {"aspect": "cpu_ram"},
        )
        self.register("screenshot", r"^(take screenshot|capture screen|screen shot)$", "take_screenshot", {})
        self.register(
            "open_browser", r"^(open browser|open chrome|launch browser)$", "open_app", {"app_name": "chrome"}
        )
        self.register(
            "open_terminal",
            r"^(open terminal|open cmd|launch terminal|open powershell)$",
            "open_app",
            {"app_name": "powershell"},
        )

    def match(self, spoken_text: str) -> Optional[Tuple[str, dict]]:
        text = spoken_text.strip()
        for key, (pattern, intent_name, args) in self._shortcuts.items():
            if pattern.search(text):
                return intent_name, args
        return None


_SHORTCUTS = VoiceShortcutRegistry()


def match_voice_shortcut(spoken_text: str) -> Optional[Tuple[str, dict]]:
    """Pure acoustic pattern matching. Produces intent signals with zero side effects."""
    return _SHORTCUTS.match(spoken_text)
