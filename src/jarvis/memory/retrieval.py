"""Gated context retrieval and progressive disclosure engine."""

from __future__ import annotations

import logging
from typing import Any

from .facts import ExplicitFact, ExplicitFactStore, FactCategory
from .summarizer import SessionSummarizer

logger = logging.getLogger("jarvis.memory.retrieval")

# Approximate 4 characters per token heuristic
DEFAULT_MAX_CONTEXT_TOKENS = 600
DEFAULT_MAX_CHARS = DEFAULT_MAX_CONTEXT_TOKENS * 4


class MemoryRetriever:
    """Context engineering engine: selects, compresses, and bounds memory for prompts."""

    def __init__(
        self,
        fact_store: ExplicitFactStore,
        summarizer: SessionSummarizer | None = None,
    ) -> None:
        self.fact_store = fact_store
        self.summarizer = summarizer

    def retrieve_context(
        self,
        query: str,
        *,
        max_chars: int = DEFAULT_MAX_CHARS,
        max_facts: int = 8,
        include_recent_summary: bool = True,
    ) -> str:
        """Construct a bounded, relevance-gated context block for model prompts."""
        selected_facts: list[ExplicitFact] = []
        seen_keys: set[tuple[str, str]] = set()

        # 1. High-priority identity facts (small, durable, core anchor)
        identity_facts = self.fact_store.list_facts(category=FactCategory.IDENTITY, enabled_only=True)
        for f in identity_facts[:2]:
            pair = (f.category.value, f.key)
            if pair not in seen_keys:
                selected_facts.append(f)
                seen_keys.add(pair)

        # 2. Query-relevant facts via gated search
        if query.strip():
            matched_facts = self.fact_store.search_facts(query, limit=max_facts, enabled_only=True)
            for f in matched_facts:
                pair = (f.category.value, f.key)
                if pair not in seen_keys:
                    selected_facts.append(f)
                    seen_keys.add(pair)

        # 3. Always include core preferences if query didn't fill budget
        if len(selected_facts) < max_facts:
            pref_facts = self.fact_store.list_facts(category=FactCategory.PREFERENCE, enabled_only=True)
            for f in pref_facts:
                pair = (f.category.value, f.key)
                if pair not in seen_keys and len(selected_facts) < max_facts:
                    selected_facts.append(f)
                    seen_keys.add(pair)

        # Format lines
        lines: list[str] = ["## Relevant Memory Context:"]
        current_len = len(lines[0]) + 1

        for f in selected_facts:
            item_line = f"- [{f.category.value.title()}] {f.key}: {f.value}"
            if current_len + len(item_line) + 1 > max_chars:
                break
            lines.append(item_line)
            current_len += len(item_line) + 1

        # 4. Compressed recent session summary (if requested and budget allows)
        if include_recent_summary and self.summarizer is not None:
            recent_summaries = self.summarizer.list_recent_summaries(limit=1)
            if recent_summaries:
                s = recent_summaries[0]
                summary_line = f"- [Recent Session] {s.summary_text}"
                if current_len + len(summary_line) + 1 <= max_chars:
                    lines.append(summary_line)

        # If only the header was generated, return empty string (don't inject noise)
        if len(lines) == 1:
            return ""

        return "\n".join(lines).strip()

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search across explicit facts and recent summaries."""
        results: list[dict[str, Any]] = []

        facts = self.fact_store.search_facts(query, limit=limit, enabled_only=True)
        for f in facts:
            results.append({
                "type": "explicit_fact",
                "category": f.category.value,
                "key": f.key,
                "value": f.value,
                "source": f.source,
            })

        if self.summarizer is not None and len(results) < limit:
            summaries = self.summarizer.list_recent_summaries(limit=3)
            q_lower = query.lower()
            for s in summaries:
                if q_lower in s.summary_text.lower():
                    results.append({
                        "type": "session_summary",
                        "session_id": s.session_id,
                        "text": s.summary_text,
                    })

        return results[:limit]
