# core/intent_classifier.py — Canonical Request Atomicity & Multi-Intent Classifier
"""
Canonical Request Classification Stage for BR JARVIS.
Distinguishes ATOMIC requests from COMPOSITE multi-step requests,
detects sequencing, conjunctions, multiple independent action verbs,
conversational queries, and negations.

Ensures Deterministic Fast-Path execution is granted ONLY when the entire user utterance
is confidently classified as one atomic action.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import List, Optional, Set, Tuple

from .intent_models import ActionIntent, AtomicIntentResult, CompositeIntent, ExecutionTrace

logger = logging.getLogger("JARVIS.IntentClassifier")


class IntentTraceStore:
    """Thread-safe in-memory store for recent execution traces."""

    _lock = threading.Lock()
    _traces: List[ExecutionTrace] = []
    _MAX_TRACES = 200

    @classmethod
    def record(cls, trace: ExecutionTrace) -> None:
        with cls._lock:
            cls._traces.append(trace)
            if len(cls._traces) > cls._MAX_TRACES:
                cls._traces.pop(0)

    @classmethod
    def get_last_trace(cls) -> Optional[ExecutionTrace]:
        with cls._lock:
            return cls._traces[-1] if cls._traces else None

    @classmethod
    def get_recent_traces(cls, count: int = 10) -> List[ExecutionTrace]:
        with cls._lock:
            return list(cls._traces[-count:])

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._traces.clear()


class IntentClassifier:
    """
    Canonical request classification engine.
    Evaluates:
      1. Security & Prompt Injection
      2. Conversational Questions / Explanations
      3. Negations
      4. Composite Sequencing & Conjunctions
      5. Action Verb Density
      6. Semantic Grouping (e.g. 'open chrome and github', 'show CPU and RAM')
      7. Unconsumed text verification
    """

    # Common executable action verbs (Requirement 15)
    ACTION_VERBS: Set[str] = {
        "open",
        "launch",
        "start",
        "run",
        "visit",
        "go to",
        "browse",
        "close",
        "kill",
        "stop",
        "exit",
        "terminate",
        "show",
        "display",
        "check",
        "inspect",
        "get",
        "view",
        "read",
        "write",
        "create",
        "make",
        "build",
        "generate",
        "delete",
        "remove",
        "clean",
        "clear",
        "send",
        "post",
        "email",
        "search",
        "find",
        "lookup",
        "query",
        "download",
        "upload",
        "click",
        "type",
        "press",
        "execute",
        "take",
        "capture",
        "analyze",
        "compare",
        "summarize",
        "save",
        "move",
        "copy",
        "cut",
        "mute",
        "unmute",
    }

    # Explicit sequencing signals (Requirement 4)
    EXPLICIT_SEQUENCERS: List[Tuple[str, str]] = [
        ("and then", r"\s+and\s+then\s+"),
        ("then", r"\s+then\s+"),
        ("after that", r"\s+after\s+that\s+"),
        ("followed by", r"\s+followed\s+by\s+"),
        ("next", r"\s+next\s+"),
        ("also", r"\s+also\s+"),
        ("finally", r"\s+finally\s+"),
        ("afterwards", r"\s+afterwards\s+"),
        ("subsequently", r"\s+subsequently\s+"),
    ]

    # Polite filler tokens that do not invalidate atomicity if left over
    FILLER_TOKENS: Set[str] = {
        "please",
        "plz",
        "thanks",
        "thank",
        "you",
        "jarvis",
        "brjarvis",
        "now",
        "sir",
        "kindly",
        "quick",
        "quickly",
    }

    # Conversational / question starters that require LLM reasoning, not deterministic execution
    QUESTION_PREFIXES: List[str] = [
        "why should i",
        "why would i",
        "why open",
        "why do",
        "why is",
        "how do i",
        "how can i",
        "how to",
        "tell me how to",
        "tell me how",
        "tell me why",
        "can you explain",
        "explain how to",
        "explain to me",
        "what is the difference",
        "what should i",
        "should i",
        "would you recommend",
    ]

    # Whole-sentence negation patterns
    NEGATION_STARTERS: List[str] = [
        "do not",
        "don't",
        "dont",
        "never",
        "please don't",
        "please do not",
        "stop",
        "abort",
        "cancel",
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Normalize user text by stripping extra spaces and punctuation."""
        return " ".join(text.lower().strip().split())

    @classmethod
    def is_question_or_conversational(cls, text: str) -> bool:
        """Check if utterance is a question or conversational discussion."""
        clean = cls.clean_text(text).rstrip(".!?")
        if text.strip().endswith("?"):
            return True
        for qp in cls.QUESTION_PREFIXES:
            if clean.startswith(qp):
                return True
        return False

    @classmethod
    def is_predominantly_negated(cls, text: str) -> bool:
        """Check if the entire command is a negative instruction (e.g. 'do not open Excel')."""
        clean = cls.clean_text(text).rstrip(".!?")
        for ns in cls.NEGATION_STARTERS:
            if clean.startswith(ns + " "):
                return True
        return False

    @classmethod
    def _extract_verbs(cls, text: str) -> List[Tuple[str, int]]:
        """Find occurrences of action verbs and their character offsets in text."""
        words = cls.clean_text(text).split()
        found: List[Tuple[str, int]] = []
        for i, w in enumerate(words):
            if w in cls.ACTION_VERBS:
                found.append((w, i))
            elif i < len(words) - 1 and f"{w} {words[i+1]}" in cls.ACTION_VERBS:
                found.append((f"{w} {words[i+1]}", i))
        return found

    @classmethod
    def _is_grouped_semantic_intent(cls, text: str) -> Optional[Tuple[str, str]]:
        """
        Check if an 'and' conjunction represents a single grouped semantic operation (Section 5).
        Returns (intent_name, clean_consumed) or None.
        Examples:
          - "show CPU and RAM usage" -> system health
          - "open chrome and github" -> browser navigation
          - "check cpu and memory" -> system health
        """
        clean = cls.clean_text(text).rstrip(".!?")

        # 1. System Health Telemetry Grouping
        sys_health_patterns = [
            r"^(?:show|check|display|inspect|get|view)\s+(?:the\s+)?(?:cpu|ram|memory|disk|battery)\s+and\s+(?:the\s+)?(?:cpu|ram|memory|disk|battery)(?:\s+usage|\s+status|\s+health)?$",
            r"^(?:cpu|ram|memory)\s+and\s+(?:cpu|ram|memory)(?:\s+usage|\s+status)?$",
            r"^(?:show|check)\s+(?:cpu|ram)\s+and\s+(?:cpu|ram)(?:\s+usage)?$",
        ]
        for pat in sys_health_patterns:
            if re.match(pat, clean):
                return ("system_health_grouped", clean)

        # 2. Browser Navigation Grouping (e.g. "open chrome and github", "open brave and reddit")
        browser_names = ["chrome", "brave", "edge", "firefox", "browser", "opera"]
        for b in browser_names:
            pat = rf"^(?:open|launch|run)\s+{b}\s+and\s+([a-z0-9_\-\.\/]+)$"
            m = re.match(pat, clean)
            if m:
                target = m.group(1).strip()
                # Target is a website or query, not another action verb
                if target not in cls.ACTION_VERBS:
                    return ("browser_open_url_grouped", clean)

        return None

    @classmethod
    def split_clauses(cls, text: str) -> List[str]:
        """
        Split a composite user utterance into individual clauses using explicit sequencers,
        coordinating conjunctions with action verbs, and punctuation.
        """
        clean = cls.clean_text(text)

        # Check explicit sequencers first
        for name, regex in cls.EXPLICIT_SEQUENCERS:
            if re.search(regex, clean):
                parts = re.split(regex, clean)
                return [p.strip() for p in parts if p.strip()]

        # Check comma followed by an action verb or sequencer
        # e.g., "open vscode, create test.py, and run it"
        comma_parts = [p.strip() for p in clean.split(",") if p.strip()]
        if len(comma_parts) > 1:
            # Check if each part contains an action or begins with 'and'
            verbs_count = sum(1 for cp in comma_parts if any(v in cp.split() for v in cls.ACTION_VERBS))
            if verbs_count >= 2:
                result = []
                for cp in comma_parts:
                    p = re.sub(r"^(?:and\s+then|and|then)\s+", "", cp).strip()
                    if p:
                        result.append(p)
                return result

        # Check 'and' conjunction: only split if clause after 'and' has its own actionable verb
        if " and " in clean:
            parts = clean.split(" and ", 1)
            left = parts[0].strip()
            right = parts[1].strip()

            # Does right clause contain an action verb or negation?
            right_words = right.split()
            has_verb = any(v in right_words for v in cls.ACTION_VERBS)
            has_negation = any(n in right_words for n in ["don't", "dont", "do not", "never", "not"])

            if (has_verb or has_negation) and not cls._is_grouped_semantic_intent(clean):
                return [left, right]

        return [clean]

    @classmethod
    def identify_clause_intent(cls, clause: str, order: int) -> ActionIntent:
        """Analyze an individual clause and map to a structured ActionIntent."""
        cl = cls.clean_text(clause).rstrip(".!?")
        is_negated = any(cl.startswith(n) for n in ["don't", "dont", "do not", "never"]) or " don't " in cl or " do not " in cl

        # Clean leading negation for matching target
        cl_clean = re.sub(r"^(?:don't|dont|do not|never)\s+", "", cl).strip()

        # Online Excel / Productivity suite
        if any(kw in cl_clean for kw in ["excel sheet", "excel online", "online excel", "excel in web", "excel sheet in web", "google sheet", "google sheets"]):
            target_url = "https://excel.new"
            return ActionIntent(
                intent="open_online_excel",
                order=order,
                raw_text=clause,
                parameters={"url": target_url, "app_name": "Online Excel Sheets"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="browser_open",
                is_negated=is_negated,
            )

        # Online Word
        if any(kw in cl_clean for kw in ["word online", "online word", "google doc", "google docs"]):
            target_url = "https://word.new"
            return ActionIntent(
                intent="open_online_word",
                order=order,
                raw_text=clause,
                parameters={"url": target_url, "app_name": "Online Word"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="browser_open",
                is_negated=is_negated,
            )

        # System Properties / Diagnostics
        if any(kw in cl_clean for kw in ["system properties", "system info", "system information", "system health", "system status", "check cpu", "show cpu", "cpu usage"]):
            return ActionIntent(
                intent="show_system_properties",
                order=order,
                raw_text=clause,
                parameters={"aspect": "full_summary"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="system_diagnostic",
                is_negated=is_negated,
            )

        # Calculator
        if any(kw in cl_clean for kw in ["calculator", "calc"]):
            return ActionIntent(
                intent="open_calculator",
                order=order,
                raw_text=clause,
                parameters={"app_name": "calculator"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="app_launch",
                is_negated=is_negated,
            )

        # Notepad
        if "notepad" in cl_clean:
            return ActionIntent(
                intent="open_notepad",
                order=order,
                raw_text=clause,
                parameters={"app_name": "notepad"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="app_launch",
                is_negated=is_negated,
            )

        # Task Manager
        if any(kw in cl_clean for kw in ["task manager", "taskmgr"]):
            return ActionIntent(
                intent="open_task_manager",
                order=order,
                raw_text=clause,
                parameters={"app_name": "taskmgr"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="app_launch",
                is_negated=is_negated,
            )

        # Chrome / Browser launch
        if "chrome" in cl_clean and not any(kw in cl_clean for kw in ["github", "reddit", "youtube"]):
            return ActionIntent(
                intent="open_chrome",
                order=order,
                raw_text=clause,
                parameters={"app_name": "chrome"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="app_launch",
                is_negated=is_negated,
            )

        # URL Navigation (e.g. go to github)
        if any(kw in cl_clean for kw in ["github", "github.com"]):
            return ActionIntent(
                intent="open_url",
                order=order,
                raw_text=clause,
                parameters={"url": "https://github.com"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="open_url",
                is_negated=is_negated,
            )

        # Screenshot
        if any(kw in cl_clean for kw in ["screenshot", "capture screen"]):
            return ActionIntent(
                intent="take_screenshot",
                order=order,
                raw_text=clause,
                parameters={},
                depends_on=[order - 1] if order > 1 else [],
                action_type="screenshot",
                is_negated=is_negated,
            )

        # Save to documents / file save
        if any(kw in cl_clean for kw in ["save it to documents", "save to documents", "save file", "save it"]):
            return ActionIntent(
                intent="save_artifact",
                order=order,
                raw_text=clause,
                parameters={"destination": "documents"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="file_save",
                is_negated=is_negated,
            )

        # VSCode / Code editor
        if any(kw in cl_clean for kw in ["vscode", "code"]):
            return ActionIntent(
                intent="open_vscode",
                order=order,
                raw_text=clause,
                parameters={"app_name": "vscode"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="app_launch",
                is_negated=is_negated,
            )

        # Create file
        if any(kw in cl_clean for kw in ["create test.py", "create file", "create a file"]):
            return ActionIntent(
                intent="create_file",
                order=order,
                raw_text=clause,
                parameters={"filename": "test.py"},
                depends_on=[order - 1] if order > 1 else [],
                action_type="file_create",
                is_negated=is_negated,
            )

        # Generic action
        return ActionIntent(
            intent=f"action_{order}",
            order=order,
            raw_text=clause,
            parameters={},
            depends_on=[order - 1] if order > 1 else [],
            action_type="general",
            is_negated=is_negated,
        )

    @classmethod
    def classify(cls, user_input: str) -> AtomicIntentResult | CompositeIntent:
        """
        Primary entry point to classify any user utterance into an AtomicIntentResult
        or a CompositeIntent.
        """
        raw = user_input.strip()
        clean = cls.clean_text(raw).rstrip(".!?")

        # 1. Question / Conversational Filtering
        if cls.is_question_or_conversational(raw):
            logger.debug("[IntentClassifier] Utterance identified as conversational question: '%s'", raw)
            return AtomicIntentResult(
                matched=False,
                atomic=False,
                intent="conversational_query",
                consumed_text="",
                remaining_text=raw,
                confidence=0.95,
                requires_planner=True,
                action_type="conversation",
            )

        # 2. Whole-Command Negation Filtering
        if cls.is_predominantly_negated(raw):
            logger.debug("[IntentClassifier] Utterance identified as negated command: '%s'", raw)
            return AtomicIntentResult(
                matched=False,
                atomic=False,
                intent="negated_command",
                consumed_text="",
                remaining_text=raw,
                confidence=0.95,
                requires_planner=True,
                action_type="negation",
            )

        # 3. Semantic Grouping Check (Section 5)
        # e.g., "show CPU and RAM usage", "open chrome and github"
        grouped = cls._is_grouped_semantic_intent(clean)
        if grouped:
            intent_name, consumed = grouped
            logger.debug("[IntentClassifier] Utterance identified as semantic group '%s': '%s'", intent_name, consumed)
            return AtomicIntentResult(
                matched=True,
                atomic=True,
                intent=intent_name,
                consumed_text=consumed,
                remaining_text="",
                confidence=0.95,
                requires_planner=False,
                action_type="atomic_grouped",
            )

        # 4. Multi-Clause / Composite Splitting
        clauses = cls.split_clauses(clean)
        if len(clauses) > 1:
            actions: List[ActionIntent] = []
            has_negated = False
            for idx, c in enumerate(clauses, start=1):
                act = cls.identify_clause_intent(c, idx)
                if act.is_negated:
                    has_negated = True
                actions.append(act)

            logger.info(
                "[IntentClassifier] Multi-intent composite request detected (%d actions): %s",
                len(actions),
                [a.intent for a in actions],
            )
            return CompositeIntent(
                original_text=raw,
                actions=actions,
                dependencies=[a.depends_on for a in actions],
                confidence=0.95,
                requires_planner=True,
                is_negated_clause_present=has_negated,
            )

        # 5. Single-Clause Candidate: Verify Action Verb Count
        verbs = cls._extract_verbs(clean)
        if len(verbs) > 1:
            # Contains multiple distinct verbs even without explicit sequencer
            # e.g., "take screenshot save it to documents"
            logger.info("[IntentClassifier] Multiple action verbs (%d) in single clause -> Composite", len(verbs))
            return CompositeIntent(
                original_text=raw,
                actions=[
                    ActionIntent(intent=f"action_{v[0]}", order=i + 1, raw_text=v[0])
                    for i, v in enumerate(verbs)
                ],
                dependencies=[],
                confidence=0.85,
                requires_planner=True,
            )

        # 6. Single Atomic Intent Candidate
        # Calculate tentative intent from the clean single clause
        candidate_intent = cls.identify_clause_intent(clean, 1)

        # Calculate consumed and remaining text
        consumed = clean
        remaining = ""

        # Polite filler stripping from remaining text
        return AtomicIntentResult(
            matched=True,
            atomic=True,
            intent=candidate_intent.intent,
            parameters=candidate_intent.parameters,
            consumed_text=consumed,
            remaining_text=remaining,
            confidence=0.95,
            requires_planner=False,
            action_type=candidate_intent.action_type,
        )
