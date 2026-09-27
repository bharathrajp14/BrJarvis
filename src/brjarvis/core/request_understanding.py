# core/request_understanding.py — Canonical Request Understanding Engine
"""
Canonical RequestUnderstandingEngine for BR JARVIS.
This engine is the sole authoritative entry point for analyzing, normalizing,
classifying atomicity, identifying actions and dependencies, detecting negations,
conditionals, hypotheticals, questions, and ambiguous references before ANY
action authorization or side effect can occur.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from brjarvis.core.intent_models import (
    AtomicityType,
    ExecutionMode,
    ProposedAction,
    RequestUnderstanding,
    RiskLevel,
)

logger = logging.getLogger("JARVIS.RequestUnderstanding")


class RequestUnderstandingEngine:
    """
    Canonical request perception, normalization, and understanding engine.
    Ensures that BRJARVIS understands the COMPLETE user request before
    proposing an action plan or authorizing side effects.
    """

    # Common filler words and speech disfluencies
    FILLER_WORDS: Set[str] = {
        "uh",
        "um",
        "ah",
        "er",
        "like",
        "you know",
        "i mean",
        "well",
        "so",
        "okay",
        "ok",
        "please",
        "kindly",
        "jarvis",
        "brjarvis",
        "hey jarvis",
    }

    # Common speech-to-text self-correction markers
    SELF_CORRECTION_PATTERNS = [
        r"(?:,\s*|\s+)(?:actually\s+no|actually|no\s+wait|wait|never\s+mind|scratch\s+that)[,\s\-]+(.+)$",
        r"-\s*(?:actually\s+no|actually|no\s+wait|wait|scratch\s+that)\s*[-,\s]?\s*(.+)$",
        r",\s*actually\s+([a-zA-Z0-9_\s]+)$",
        r"\s+-\s+wait\s+-\s+([a-zA-Z0-9_\s]+)$",
    ]

    # Action verbs defining potentially executable instructions
    ACTION_VERBS: Set[str] = {
        "open", "launch", "start", "run", "visit", "browse", "go to",
        "close", "kill", "stop", "exit", "terminate",
        "show", "display", "check", "inspect", "get", "view", "read",
        "write", "create", "make", "build", "generate",
        "delete", "remove", "clean", "clear", "wipe", "format",
        "send", "post", "email", "message",
        "search", "find", "lookup", "query",
        "download", "upload", "fetch",
        "click", "type", "press", "input",
        "execute", "call", "invoke",
        "take", "capture", "screenshot",
        "analyze", "compare", "summarize", "explain", "tell", "ask",
        "save", "move", "copy", "cut",
        "mute", "unmute", "volume",
        "restart", "reboot", "shutdown", "poweroff", "sleep", "lock",
        "install", "uninstall", "update", "upgrade",
        "fix", "patch", "test",
        "play", "research", "backup", "monitor", "deploy",
    }

    # Ordering and sequencing signals
    SEQUENCERS = [
        "and then", "followed by", "after that", "after this",
        "then", "next", "subsequently", "afterwards", "finally",
        "after", "before", "once",
    ]

    # Conditional markers
    CONDITIONAL_MARKERS = [
        "if", "unless", "only if", "provided that", "in case",
        "otherwise", "or else", "until", "when failed", "if fails",
        "if it fails", "if failure",
    ]

    # Iterative / recurring markers
    ITERATIVE_MARKERS = [
        "every morning", "every day", "every night", "every 5 minutes",
        "every hour", "every week", "every month", "every", "daily",
        "weekly", "hourly", "nightly", "each morning", "each day",
    ]

    # Whole-sentence negation patterns
    NEGATION_MARKERS = [
        "don't", "dont", "do not", "never", "avoid", "stop",
        "cancel", "abort", "without", "prohibit", "disallow",
    ]

    # Informational / question indicators
    QUESTION_STARTERS = [
        "how do i", "how can i", "how to", "tell me how",
        "why would i", "why should i", "why is", "why do",
        "what is", "what are", "what happens if", "what would happen if",
        "can you explain", "explain to me", "explain whether", "explain if",
        "should i", "would you recommend", "is it possible to",
        "tell me whether", "tell me if",
    ]

    # Hypothetical indicators
    HYPOTHETICAL_MARKERS = [
        "pretend you", "pretend that", "simulate", "what if",
        "what would happen if", "hypothetically", "imagine that",
        "suppose you", "as an exercise",
    ]

    # Pronouns and references requiring contextual resolution
    AMBIGUOUS_PRONOUNS = {
        "it", "that", "this", "there", "them", "the file", "the document",
        "the previous one", "the same site", "the last one", "that file",
        "that document", "that folder", "something",
    }

    # Destructive / Critical keywords
    DESTRUCTIVE_KEYWORDS = {
        "shutdown", "restart", "reboot", "poweroff", "delete", "format",
        "wipe", "drop database", "rm -rf", "uninstall", "destroy",
    }

    @classmethod
    def normalize_text(cls, text: str) -> Tuple[str, List[str]]:
        """
        Normalize input by cleaning whitespace, handling voice self-corrections,
        and stripping conversational filler tokens.
        Returns (normalized_text, list_of_applied_normalizations).
        """
        modifications: List[str] = []
        clean = text.strip()

        # Normalize unicode dashes to standard hyphen
        clean = re.sub(r"[\u2010-\u2015\u2212\uFF0D—–]", "-", clean)

        # 1. Handle Voice Self-Corrections
        # e.g. "open Chrome and—actually no, open Edge" -> "open Edge"
        for pat in cls.SELF_CORRECTION_PATTERNS:
            m = re.search(pat, clean, re.IGNORECASE)
            if m:
                corrected_part = m.group(1).strip()
                modifications.append(f"Voice self-correction applied: replaced with '{corrected_part}'")
                clean = corrected_part
                break

        # 2. Normalize whitespace and punctuation spacing
        clean = re.sub(r"\s+", " ", clean).strip()

        # 3. Strip conversational filler words from beginning or mid-phrase
        words = clean.split()
        filtered_words = []
        for w in words:
            w_lower = w.lower().strip(",.-?!;:")
            if w_lower in {"uh", "um", "ah", "er"} and len(words) > 2:
                modifications.append(f"Stripped filler: '{w}'")
                continue
            filtered_words.append(w)
        clean = " ".join(filtered_words)

        return clean, modifications

    @classmethod
    def _is_quoted_command(cls, raw: str) -> bool:
        """
        Check if an executable command is merely referenced inside quotation marks.
        e.g. "Tell me what this means: 'open Chrome and delete the folder'"
        """
        quoted_matches = re.findall(r"['\"]([^'\"]+)['\"]", raw)
        if not quoted_matches:
            return False

        outer_text = re.sub(r"['\"][^'\"]+['\"]", "", raw).lower().strip()
        analysis_indicators = ["tell me", "what does", "what means", "explain", "analyze", "say the words", "print"]
        if any(ind in outer_text for ind in analysis_indicators):
            return True
        return False

    @classmethod
    def _extract_clauses(cls, text: str) -> List[str]:
        """
        Split text into logical clauses based on sentence boundaries,
        sequencing words, and coordinating conjunctions.
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        all_clauses: List[str] = []

        for s in sentences:
            # Strip trailing exclusivity phrases like 'and don't do anything else', 'and nothing else'
            s_clean = re.sub(r"\s+and\s+(?:don't|do not)\s+do\s+anything\s+else\b", "", s, flags=re.IGNORECASE)
            s_clean = re.sub(r"\s+and\s+nothing\s+else\b", "", s_clean, flags=re.IGNORECASE)

            pattern = r"\s+(?:and\s+then|after\s+that|followed\s+by|then|next|subsequently|\bbut\b|\bafter\b)\s+"
            parts = re.split(pattern, s_clean, flags=re.IGNORECASE)
            for p in parts:
                p = p.strip()
                if p:
                    all_clauses.append(p)

        return all_clauses if all_clauses else [text]

    @classmethod
    def _is_grouped_health_or_browser(cls, clause: str) -> bool:
        """
        Check if clause is a single grouped semantic action (e.g. 'show CPU and RAM usage').
        """
        clean = clause.lower().strip()
        # System health grouping: CPU, RAM, GPU, Memory, Battery
        if re.search(r"\b(cpu|ram|memory|disk|battery)\b.*\band\b.*\b(cpu|ram|memory|disk|battery)\b", clean):
            return True
        # Browser URL grouping: "open chrome and github" (only when right side has no secondary action verb)
        m = re.search(r"\b(open|launch)\s+(chrome|edge|brave|firefox)\s+and\s+([a-z0-9_\-\.\/]+)$", clean)
        if m:
            right = m.group(3).lower()
            if right not in cls.ACTION_VERBS and not any(v in right for v in ["search", "delete", "run", "open", "kill", "visit"]):
                return True
        return False

    @classmethod
    def _detect_action_intent(cls, clause: str, order: int) -> Optional[ProposedAction]:
        """Convert a single clause into a ProposedAction if an actionable verb is present."""
        clean = clause.lower().strip()
        words = clean.split()

        # Check for negation in clause
        is_neg = any(clean.startswith(nm + " ") or f" {nm} " in f" {clean} " for nm in cls.NEGATION_MARKERS)

        # Check for condition in clause
        is_cond = any(f" {cm} " in f" {clean} " or clean.startswith(cm + " ") for cm in cls.CONDITIONAL_MARKERS)

        # Detect primary verb
        action_verb = None
        for w in words:
            w_clean = w.strip(",.-?!")
            if w_clean in cls.ACTION_VERBS:
                action_verb = w_clean
                break
            if w_clean.endswith("ing"):
                stem = w_clean[:-3]
                if stem in cls.ACTION_VERBS:
                    action_verb = stem
                    break
                if len(stem) > 2 and stem[-1] == stem[-2] and stem[:-1] in cls.ACTION_VERBS:
                    action_verb = stem[:-1]
                    break

        if not action_verb:
            # Check for implicit action verbs (e.g. "excel sheet in web", "system properties", standalone app name)
            if "excel" in clean or "sheet" in clean:
                action_verb = "open"
            elif "system properties" in clean or "system info" in clean:
                action_verb = "show"
            elif clean in ("edge", "chrome", "notepad", "calculator", "calc", "vscode", "spotify", "word"):
                action_verb = "open"
            elif "github" in clean or "google" in clean or "bing" in clean:
                action_verb = "visit"
            elif clean.startswith("tell me") or clean.startswith("explain"):
                action_verb = "explain"
            elif "report" in clean or "document" in clean or "database" in clean or "inbox" in clean:
                action_verb = "action"

        if not action_verb and not is_neg:
            return None

        # Determine risk level
        risk = RiskLevel.LOW
        if any(dk in clean for dk in cls.DESTRUCTIVE_KEYWORDS):
            risk = RiskLevel.CRITICAL
        elif action_verb in ("delete", "remove", "write", "kill", "format", "backup", "deploy"):
            risk = RiskLevel.HIGH
        elif action_verb in ("open", "launch", "download", "send", "execute", "play"):
            risk = RiskLevel.MEDIUM

        action = ProposedAction(
            action_id=f"act_{uuid.uuid4().hex[:8]}",
            intent=f"{action_verb or 'action'}_{order}",
            tool="native_os",
            parameters={"raw_clause": clause, "verb": action_verb},
            order=order,
            raw_text=clause,
            execution_mode=ExecutionMode.SEQUENTIAL,
            is_negated=is_neg,
            is_conditional=is_cond,
            risk_level=risk,
            verification_strategy="universal_verifier",
        )
        return action

    @classmethod
    def understand(
        cls,
        raw_input: str,
        streaming_status: str = "input_final",
        context: Optional[Dict[str, Any]] = None,
    ) -> RequestUnderstanding:
        """
        Analyze the full request and generate the authoritative RequestUnderstanding.
        Zero side-effects occur inside this analysis.
        """
        request_id = f"req_{uuid.uuid4().hex[:10]}"
        raw_trimmed = (raw_input or "").strip()

        # Handle empty input
        if not raw_trimmed:
            return RequestUnderstanding(
                request_id=request_id,
                raw_input="",
                normalized_input="",
                atomicity=AtomicityType.AMBIGUOUS,
                confidence=1.0,
                completeness_score=0.0,
                requires_clarification=True,
                unresolved_parts=["Empty input received"],
            )

        # ── 1. Streaming Perception Gate ───────────────────────────────────────
        if streaming_status != "input_final":
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=raw_trimmed,
                atomicity=AtomicityType.AMBIGUOUS,
                confidence=0.5,
                requires_planner=False,
                deterministic_eligible=False,
                unresolved_parts=["Streaming input in progress (not final)"],
                completeness_score=0.3,
            )

        # ── 2. Normalization & Voice Self-Correction ───────────────────────────
        normalized, modifications = cls.normalize_text(raw_trimmed)
        clean_lower = normalized.lower().strip()

        # ── 2b. Truncated / Incomplete Utterance Guard (Red-Team) ─────────────
        has_trailing_ellipsis = raw_trimmed.endswith("...") or raw_trimmed.endswith("..")
        clean_no_punct = clean_lower.rstrip(".!? ")
        ends_with_incomplete_clause = any(
            clean_no_punct.endswith(f" {tok}") for tok in ["then", "and then", "if", "unless", "but don't", "actually", "after that"]
        ) or clean_no_punct in ("if", "and then", "then", "but don't")
        if has_trailing_ellipsis or ends_with_incomplete_clause:
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=normalized,
                intent_type="incomplete_request",
                atomicity=AtomicityType.CONDITIONAL if "if" in clean_lower else AtomicityType.AMBIGUOUS,
                confidence=0.7,
                requires_clarification=True,
                deterministic_eligible=False,
                completeness_score=0.3,
                unresolved_parts=["Input appears incomplete with trailing ellipsis or unconsumed conjunction/condition"],
            )

        # ── 3. Quoted Command Analysis ─────────────────────────────────────────
        if cls._is_quoted_command(raw_trimmed):
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=normalized,
                intent_type="quote_analysis",
                atomicity=AtomicityType.INFORMATIONAL,
                confidence=0.98,
                requires_planner=True,
                deterministic_eligible=False,
                completeness_score=1.0,
                questions=[raw_trimmed],
            )

        # ── 4. Hypothetical Analysis ───────────────────────────────────────────
        if any(clean_lower.startswith(hm) or f" {hm} " in f" {clean_lower} " for hm in cls.HYPOTHETICAL_MARKERS):
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=normalized,
                intent_type="hypothetical_inquiry",
                atomicity=AtomicityType.HYPOTHETICAL,
                confidence=0.95,
                requires_planner=True,
                deterministic_eligible=False,
                completeness_score=1.0,
            )

        # ── 5. Pure Question vs Command Analysis ───────────────────────────────
        has_sequencers = any(f" {seq} " in f" {clean_lower} " for seq in ["then", "and then", "after that", "next"])
        has_sentences = len([s for s in re.split(r"[.!?]+", clean_lower) if s.strip()]) > 1

        is_pure_question = False
        if not has_sequencers and not has_sentences:
            if clean_lower.endswith("?") or any(clean_lower.startswith(qs) for qs in cls.QUESTION_STARTERS):
                is_pure_question = True

        if is_pure_question:
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=normalized,
                intent_type="informational_query",
                atomicity=AtomicityType.INFORMATIONAL,
                confidence=0.95,
                requires_planner=True,
                deterministic_eligible=False,
                completeness_score=1.0,
                questions=[normalized],
            )

        # ── 6. Whole-Sentence Negation Analysis ────────────────────────────────
        is_whole_negated = any(clean_lower.startswith(nm + " ") or clean_lower == nm for nm in cls.NEGATION_MARKERS)
        if is_whole_negated:
            return RequestUnderstanding(
                request_id=request_id,
                raw_input=raw_trimmed,
                normalized_input=normalized,
                intent_type="negated_command",
                atomicity=AtomicityType.NEGATED,
                confidence=0.95,
                requires_planner=False,
                deterministic_eligible=False,
                completeness_score=1.0,
                negations=[normalized],
            )

        # ── 7. Conversational Salutations ──────────────────────────────────────
        conversational_salutations = {"hello", "hi", "hey", "good morning", "good evening", "good afternoon"}
        clean_greeting = re.sub(r"\b(jarvis|brjarvis|sir)\b", "", clean_no_punct).strip()
        if (
            clean_greeting in conversational_salutations
            or any(clean_greeting.startswith(cs) for cs in conversational_salutations)
        ):
            words = clean_greeting.split()
            if len(words) <= 4 and not any(w in cls.ACTION_VERBS for w in words):
                return RequestUnderstanding(
                    request_id=request_id,
                    raw_input=raw_trimmed,
                    normalized_input=normalized,
                    intent_type="conversational",
                    atomicity=AtomicityType.CONVERSATIONAL,
                    confidence=0.99,
                    requires_planner=False,
                    deterministic_eligible=False,
                    completeness_score=1.0,
                )

        # ── 8. Ambiguous Reference / Pronoun Gate ──────────────────────────────
        words = clean_lower.split()
        if len(words) <= 5:
            has_ambiguous_pronoun = any(
                f" {p} " in f" {clean_lower} " or clean_lower.startswith(p + " ") or clean_lower.endswith(" " + p) or clean_lower == p
                for p in cls.AMBIGUOUS_PRONOUNS
            )
            context_has_target = bool(context and (context.get("last_file") or context.get("target")))
            if has_ambiguous_pronoun and not context_has_target:
                return RequestUnderstanding(
                    request_id=request_id,
                    raw_input=raw_trimmed,
                    normalized_input=normalized,
                    intent_type="ambiguous_reference",
                    atomicity=AtomicityType.AMBIGUOUS,
                    confidence=0.9,
                    requires_clarification=True,
                    deterministic_eligible=False,
                    references=[p for p in cls.AMBIGUOUS_PRONOUNS if p in clean_lower],
                    unresolved_parts=["Target pronoun/reference is ambiguous and unresolved"],
                    completeness_score=0.4,
                )

        # ── 9. Clause Extraction & Semantic Grouping ───────────────────────────
        raw_clauses = cls._extract_clauses(normalized)
        actions: List[ProposedAction] = []
        conditions: List[str] = []
        negations: List[str] = []
        ordering_signals: List[str] = []

        # Check for sequencing keywords (longer first to prevent substring duplicates)
        for seq in sorted(cls.SEQUENCERS, key=len, reverse=True):
            if f" {seq} " in f" {clean_lower} ":
                if not any(seq in osig for osig in ordering_signals):
                    ordering_signals.append(seq)

        # Check for conditional language
        for cond in cls.CONDITIONAL_MARKERS:
            if f" {cond} " in f" {clean_lower} " or clean_lower.startswith(cond + " "):
                conditions.append(cond)

        # Check for iterative language
        is_iterative = any(f" {im} " in f" {clean_lower} " or clean_lower.endswith(im) for im in cls.ITERATIVE_MARKERS)

        # Process clauses
        for idx, clause in enumerate(raw_clauses, start=1):
            # Check if this clause is a grouped action (e.g. "show CPU and RAM usage")
            if cls._is_grouped_health_or_browser(clause):
                act = ProposedAction(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    intent="grouped_operation",
                    tool="system_diagnostics",
                    parameters={"clause": clause},
                    order=idx,
                    raw_text=clause,
                    execution_mode=ExecutionMode.SEQUENTIAL,
                    verification_strategy="diagnostic_verifier",
                )
                actions.append(act)
                continue

            # Check if clause has sub-actions joined by 'and'
            # e.g., "open excel and show system properties"
            if " and " in clause.lower() and not cls._is_grouped_health_or_browser(clause):
                sub_parts = clause.split(" and ")
                has_two_intents = False
                left, right = sub_parts[0].strip(), sub_parts[1].strip()
                v_left = any(v in left.lower().split() for v in cls.ACTION_VERBS) or "excel" in left.lower()
                v_right = any(v in right.lower().split() for v in cls.ACTION_VERBS) or "properties" in right.lower()

                if v_left and v_right:
                    has_two_intents = True
                    act1 = cls._detect_action_intent(left, len(actions) + 1)
                    if act1:
                        actions.append(act1)
                    act2 = cls._detect_action_intent(right, len(actions) + 1)
                    if act2:
                        act2.depends_on = [act1.action_id] if act1 else []
                        actions.append(act2)

                if has_two_intents:
                    continue

            # Standard clause action
            act = cls._detect_action_intent(clause, len(actions) + 1)
            if act:
                if act.is_negated:
                    negations.append(clause)
                if len(actions) > 0:
                    act.depends_on = [actions[-1].action_id]
                actions.append(act)

        # ── 10. Atomicity Classification ───────────────────────────────────────
        action_count = len(actions)
        if conditions:
            atomicity = AtomicityType.CONDITIONAL
        elif is_iterative:
            atomicity = AtomicityType.ITERATIVE
        elif action_count > 1:
            atomicity = AtomicityType.COMPOSITE
        elif action_count == 1:
            if actions[0].is_negated:
                atomicity = AtomicityType.NEGATED
            else:
                atomicity = AtomicityType.ATOMIC
        else:
            atomicity = AtomicityType.AMBIGUOUS

        # ── 11. Completeness Score Calculation ─────────────────────────────────
        completeness = 1.0
        if not actions and atomicity not in (AtomicityType.CONVERSATIONAL, AtomicityType.INFORMATIONAL):
            completeness -= 0.5
        if conditions:
            completeness -= 0.1
        if negations:
            completeness -= 0.05
        completeness_score = max(0.0, min(1.0, completeness))

        # ── 12. Deterministic Fast-Path Eligibility (Section 21) ───────────────
        deterministic_eligible = False
        if (
            atomicity == AtomicityType.ATOMIC
            and action_count == 1
            and not conditions
            and not negations
            and not is_pure_question
            and completeness_score >= 0.85
            and actions[0].risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
        ):
            deterministic_eligible = True

        requires_planner = not deterministic_eligible and atomicity in (
            AtomicityType.COMPOSITE,
            AtomicityType.CONDITIONAL,
            AtomicityType.ITERATIVE,
            AtomicityType.INFORMATIONAL,
            AtomicityType.HYPOTHETICAL,
        )

        overall_risk = "LOW"
        if any(a.risk_level == RiskLevel.CRITICAL for a in actions):
            overall_risk = "CRITICAL"
        elif any(a.risk_level == RiskLevel.HIGH for a in actions):
            overall_risk = "HIGH"
        elif any(a.risk_level == RiskLevel.MEDIUM for a in actions):
            overall_risk = "MEDIUM"

        return RequestUnderstanding(
            request_id=request_id,
            raw_input=raw_trimmed,
            normalized_input=normalized,
            language="en",
            intent_type=actions[0].intent if actions else atomicity.value.lower(),
            atomicity=atomicity,
            confidence=0.95 if action_count > 0 else 0.8,
            action_count=action_count,
            actions=actions,
            dependencies=[a.depends_on for a in actions if a.depends_on],
            ordering=ordering_signals,
            conditions=conditions,
            constraints=[],
            negations=negations,
            questions=[normalized] if is_pure_question else [],
            references=[],
            unresolved_parts=[],
            ignored_parts=modifications,
            requires_planner=requires_planner,
            requires_clarification=(atomicity == AtomicityType.AMBIGUOUS),
            requires_confirmation=(overall_risk in ("HIGH", "CRITICAL")),
            deterministic_eligible=deterministic_eligible,
            risk_level=overall_risk,
            privacy_level="PUBLIC",
            completeness_score=completeness_score,
        )
