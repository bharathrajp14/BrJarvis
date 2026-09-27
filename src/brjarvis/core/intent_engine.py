# core/intent_engine.py — BR JARVIS Deterministic Signal Extractor
"""
Deterministic Signal Extractor for BR JARVIS.
Pure classifier and parameter extractor with ZERO side effects.

Responsibilities:
  - Identify application names and aliases
  - Identify URLs, web destinations, and query strings
  - Identify obvious command vocabulary and verbs
  - Identify potential named entities
  - Normalize phrases and clauses
  - Extract candidate parameters into IntentCandidate

INVARIANT:
  This module NEVER launches applications, opens browsers, runs subprocesses,
  modifies files, alters system settings, or performs network side effects.
"""

from __future__ import annotations

import logging
import re
import time as _time
from typing import Any, Dict, List, Optional, Set

from brjarvis.core.intent_classifier import IntentClassifier, IntentTraceStore
from brjarvis.core.intent_models import (
    AtomicIntentResult,
    ExecutionTrace,
    IntentCandidate,
)

logger = logging.getLogger("JARVIS.SignalExtractor")


class DeterministicSignalExtractor:
    """Pure classifier and signal extractor for low-latency routing with ZERO side effects."""

    _DEDUP_CACHE: dict[str, float] = {}
    _DEDUP_TTL: float = 5.0

    @classmethod
    def _dedup_check(cls, target: str) -> bool:
        """Returns True if the target was recently registered in cache (for tracking/tests)."""
        now = _time.monotonic()
        expired = [k for k, ts in cls._DEDUP_CACHE.items() if (now - ts) > cls._DEDUP_TTL]
        for k in expired:
            del cls._DEDUP_CACHE[k]
        key = target.lower().strip()
        if key in cls._DEDUP_CACHE:
            return True
        cls._DEDUP_CACHE[key] = now
        return False

    APP_MAPPINGS: Dict[str, List[str]] = {
        "excel": ["excel", "excel.exe", "ms-excel"],
        "word": ["winword", "winword.exe", "ms-word"],
        "powerpoint": ["powerpnt", "powerpnt.exe", "ms-powerpoint"],
        "notepad": ["notepad", "notepad.exe"],
        "calculator": ["calc", "calc.exe"],
        "calc": ["calc", "calc.exe"],
        "chrome": ["chrome", "chrome.exe"],
        "brave": ["brave", "brave.exe"],
        "firefox": ["firefox", "firefox.exe"],
        "browser": ["msedge", "chrome"],
        "edge": ["msedge", "msedge.exe"],
        "vscode": ["code", "code.cmd"],
        "code": ["code", "code.cmd"],
        "terminal": ["cmd", "powershell", "wt"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe"],
        "spotify": ["spotify", "spotify.exe"],
        "paint": ["mspaint", "mspaint.exe"],
        "taskmgr": ["taskmgr", "taskmgr.exe"],
        "task manager": ["taskmgr", "taskmgr.exe"],
        "explorer": ["explorer", "explorer.exe"],
        "file explorer": ["explorer", "explorer.exe"],
        "settings": ["ms-settings:"],
        "control panel": ["control"],
        "vlc": ["vlc", "vlc.exe"],
        "snipping tool": ["snippingtool", "snippingtool.exe"],
        "wordpad": ["write", "write.exe"],
    }

    URL_SHORTCUTS: Dict[str, str] = {
        "excel": "https://excel.new",
        "excel sheet": "https://excel.new",
        "excel online": "https://excel.new",
        "online excel": "https://excel.new",
        "word": "https://word.new",
        "word online": "https://word.new",
        "online word": "https://word.new",
        "github": "https://github.com",
        "google": "https://google.com",
        "youtube": "https://youtube.com",
        "docs": "https://docs.new",
        "sheets": "https://sheets.new",
        "slides": "https://slides.new",
    }

    COMMAND_VERBS: Set[str] = {
        "open", "launch", "start", "run", "visit", "browse", "go to",
        "show", "display", "check", "inspect", "get", "view", "read",
        "close", "kill", "stop", "exit", "terminate",
        "create", "make", "write", "build", "generate",
        "delete", "remove", "clean", "clear",
        "screenshot", "capture", "search", "find",
    }

    @classmethod
    def normalize_phrase(cls, text: str) -> str:
        """Normalize phrase for signal extraction."""
        t = (text or "").strip().lower()
        t = re.sub(r"[!?,.]+$", "", t)
        t = re.sub(r"\s+", " ", t)
        return t

    @classmethod
    def extract_app_names(cls, text: str) -> List[str]:
        """Identify candidate desktop applications mentioned in text."""
        norm = cls.normalize_phrase(text)
        found: List[str] = []
        for app_name, aliases in cls.APP_MAPPINGS.items():
            for alias in aliases:
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, norm):
                    if app_name not in found:
                        found.append(app_name)
                    break
        return found

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Identify explicit URLs and known destination web shortcuts."""
        norm = cls.normalize_phrase(text)
        urls: List[str] = []
        explicit = re.findall(r"https?://[^\s]+", text)
        for u in explicit:
            urls.append(u.rstrip(".,;!"))

        for key, target_url in cls.URL_SHORTCUTS.items():
            if re.search(rf"\b{re.escape(key)}\b", norm):
                if any(w in norm for w in ("online", "web", "browser", "site", "page", ".new")):
                    if target_url not in urls:
                        urls.append(target_url)
        return urls

    @classmethod
    def extract_command_vocab(cls, text: str) -> List[str]:
        """Identify action verbs and command vocabulary present in text."""
        norm = cls.normalize_phrase(text)
        words = set(re.findall(r"\b\w+\b", norm))
        return sorted(list(words.intersection(cls.COMMAND_VERBS)))

    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """Identify prospective entities (quoted strings, path-like items, filenames)."""
        entities: List[str] = []
        quotes = re.findall(r'["\']([^"\']+)["\']', text)
        entities.extend(quotes)
        paths = re.findall(r'[a-zA-Z]:\\[^\s]+|\b\w+\.\w{2,4}\b', text)
        for p in paths:
            if p not in entities and not p.startswith("http"):
                entities.append(p)
        return entities

    @classmethod
    def extract_signals(cls, text: str) -> IntentCandidate:
        """
        Extract all semantic candidate signals from user input.
        Does NOT execute any action or trigger side effects.
        """
        norm = cls.normalize_phrase(text)
        apps = cls.extract_app_names(norm)
        urls = cls.extract_urls(norm)
        vocab = cls.extract_command_vocab(norm)
        entities = cls.extract_entities(text)

        is_question = norm.endswith("?") or any(norm.startswith(q) for q in ("how", "what", "why", "when", "where", "can you", "could you", "should i"))
        is_negated = any(norm.startswith(n) for n in ("don't", "dont", "do not", "never", "stop", "cancel"))
        is_composite = any(s in norm for s in (" and then ", " then ", " followed by ", " after that ")) or (len(vocab) > 1 and len(apps) > 1)

        candidate = IntentCandidate(
            matched=bool(apps or urls or vocab),
            entities=entities,
            app_names=apps,
            urls=urls,
            command_vocab=vocab,
            is_question=is_question,
            is_negated=is_negated,
            is_composite=is_composite,
            consumed_text=text,
            remaining_text="",
        )

        if apps and not urls:
            candidate.intent = f"open_{apps[0]}"
            candidate.action_type = "app_launch"
            candidate.target = apps[0]
            candidate.parameters = {"app_name": apps[0]}
            candidate.confidence = 0.9 if not is_question and not is_negated else 0.4
        elif urls:
            candidate.intent = "open_url"
            candidate.action_type = "browser_open"
            candidate.target = urls[0]
            candidate.parameters = {"url": urls[0]}
            candidate.confidence = 0.9 if not is_question and not is_negated else 0.4
        elif "screenshot" in vocab:
            candidate.intent = "take_screenshot"
            candidate.action_type = "screenshot"
            candidate.confidence = 0.85
        elif any(diag in norm for diag in ("system properties", "system info", "cpu", "ram", "diagnostics")):
            candidate.intent = "show_system_properties"
            candidate.action_type = "system_diagnostic"
            candidate.confidence = 0.85

        return candidate

    @classmethod
    def parse_atomic_intent(cls, text: str) -> AtomicIntentResult:
        """Classify atomic intent via IntentClassifier (pure classification, NO side effects)."""
        res = IntentClassifier.classify(text)
        if isinstance(res, AtomicIntentResult):
            return res
        return AtomicIntentResult(
            matched=True,
            atomic=False,
            intent="composite_task",
            consumed_text="",
            remaining_text=text,
            confidence=0.95,
            requires_planner=True,
        )

    @classmethod
    def parse_candidate(cls, text: str) -> IntentCandidate:
        """Alias for extract_signals."""
        return cls.extract_signals(text)

    @classmethod
    def parse_and_execute(cls, text: str) -> dict | None:
        """
        Compatibility shim: classifies via IntentClassifier and returns None for
        composite / conversational / negated requests so callers cannot bypass
        the CanonicalRequestRuntime pipeline for multi-step queries.

        For atomic deterministic requests this method:
          1. Classifies with IntentClassifier
          2. Records an IntentTraceStore trace
          3. Delegates actual side-effect execution to CanonicalRequestRuntime
          4. Returns a result dict with the *semantic* intent name (e.g. 'open_online_excel')
        """
        import time as _t
        from brjarvis.core.intent_classifier import IntentClassifier, IntentTraceStore
        from brjarvis.core.intent_models import AtomicIntentResult, CompositeIntent, ExecutionTrace

        # ── Stage 1: Classify ─────────────────────────────────────────────────
        classification = IntentClassifier.classify(text)

        # Composite / planner-required → MUST NOT execute deterministically
        if isinstance(classification, CompositeIntent) or getattr(classification, "requires_planner", False):
            trace_composite = ExecutionTrace(
                user_input=text,
                classification="composite",
                atomic=False,
                deterministic=False,
                intent="composite_or_conversational",
                planner_required=True,
                execution_started=_t.monotonic(),
            )
            IntentTraceStore.record(trace_composite)
            logger.debug(
                "[SignalExtractor] parse_and_execute returning None for composite/conversational input: '%s'",
                text,
            )
            return None

        # Atomic request — record trace and delegate execution
        assert isinstance(classification, AtomicIntentResult)
        semantic_intent = classification.intent
        t_start = _t.monotonic()

        trace = ExecutionTrace(
            user_input=text,
            classification="atomic",
            atomic=True,
            deterministic=True,
            intent=semantic_intent,
            planner_required=False,
            execution_started=t_start,
        )
        IntentTraceStore.record(trace)

        # ── Stage 2: Execute via CanonicalRequestRuntime ───────────────────────
        try:
            from brjarvis.core.canonical_runtime import CanonicalRequestRuntime
            from brjarvis.core.intent_models import ExecutionState

            resp = CanonicalRequestRuntime.handle(text)
            if resp.state == ExecutionState.COMPLETED and resp.records:
                rec = resp.records[0]
                target = (
                    rec.parameters.get("app_name")
                    or rec.parameters.get("url")
                    or rec.parameters.get("verb", "action")
                )
                return {
                    "executed": True,
                    "intent": semantic_intent,   # use IntentClassifier's semantic name
                    "target": target,
                    "result": resp.text,
                    "verified": True,
                    "records": [r.to_dict() for r in resp.records],
                }
        except Exception as exc:
            logger.debug("[SignalExtractor] CanonicalRuntime delegation error: %s", exc)

        return None


# Canonical and backward-compatibility aliases
DeterministicIntentEngine = DeterministicSignalExtractor
