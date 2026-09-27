"""Canonical UnifiedMemory facade resolving single-store cross-surface memory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .db import Database
from .facts import ExplicitFact, ExplicitFactStore, FactCategory
from .retrieval import MemoryRetriever
from .schema import initialize_database
from .store import SessionRepository, TaskRepository
from .summarizer import SessionSummarizer, SessionSummary
from .temporal import TemporalEngine

logger = logging.getLogger("jarvis.memory.unified")


class UnifiedMemory:
    """The single canonical memory facade for all BRJARVIS presentation surfaces."""

    def __init__(self, db: Database | Path | str | None = None) -> None:
        if isinstance(db, (str, Path)):
            self.db = Database(Path(db))
        elif isinstance(db, Database):
            self.db = db
        else:
            # Default to in-memory or standard location
            from jarvis.core.paths import PathLayout

            layout = PathLayout.from_project()
            layout.ensure_directories()
            self.db = Database(layout.data_root / "jarvis.db")

        # Ensure schema is migrated
        initialize_database(self.db)

        # Core subsystems
        self.facts = ExplicitFactStore(self.db)
        self.summarizer = SessionSummarizer(self.db, self.facts)
        self.retriever = MemoryRetriever(self.facts, self.summarizer)
        self.tasks = TaskRepository(self.db)
        self.sessions = SessionRepository(self.db)
        self.temporal = TemporalEngine(self.db)

    # ── Convenience API across surfaces ──────────────────────────────────────

    def remember(
        self,
        key: str,
        value: str,
        category: str = "custom",
        sensitive: bool = False,
        source: str = "user_explicit",
    ) -> ExplicitFact:
        """Record an explicit user fact."""
        return self.facts.set_fact(
            category=category,
            key=key,
            value=value,
            sensitive=sensitive,
            source=source,
        )

    def recall(self, query: str, max_chars: int = 2400) -> str:
        """Retrieve bounded, relevant context for model prompt injection."""
        return self.retriever.retrieve_context(query, max_chars=max_chars)

    def get_profile(self) -> dict[str, str]:
        """Return user profile and preferences as a flat dictionary."""
        identity = self.facts.list_facts(category=FactCategory.IDENTITY)
        prefs = self.facts.list_facts(category=FactCategory.PREFERENCE)
        profile = {f.key: f.value for f in identity}
        for p in prefs:
            profile[p.key] = p.value
            profile[f"pref.{p.key}"] = p.value
        return profile

    def set_preference(self, key: str, value: str) -> ExplicitFact:
        """Store or update a user preference."""
        return self.facts.set_fact(FactCategory.PREFERENCE, key, value)

    def get_preference(self, key: str, default: str = "") -> str:
        """Retrieve a specific user preference."""
        fact = self.facts.get_fact(FactCategory.PREFERENCE, key)
        return fact.value if fact and fact.enabled else default

    def list_facts(
        self,
        category: str | None = None,
        enabled_only: bool = True,
        include_sensitive: bool = True,
    ) -> list[dict[str, Any]]:
        """List facts for UI inspection and consent management."""
        cat_enum = FactCategory.from_str(category) if category else None
        facts = self.facts.list_facts(
            category=cat_enum,
            enabled_only=enabled_only,
            include_sensitive=include_sensitive,
        )
        return [f.to_dict() for f in facts]

    def list_all_facts(self, include_disabled: bool = True) -> list[ExplicitFact]:
        """Return all raw fact objects across categories."""
        return self.facts.list_facts(enabled_only=not include_disabled)

    def delete_fact(self, fact_id_or_category: str, key: str | None = None) -> bool:
        """Delete fact by (category, key) or by unique fact ID or key."""
        if key is not None:
            return self.facts.delete_fact(fact_id_or_category, key)
        if self.facts.delete_by_id(fact_id_or_category):
            return True
        return self.facts.delete_by_key(fact_id_or_category)

    def toggle_fact(
        self,
        fact_id_or_category: str,
        key_or_enabled: str | bool | None = None,
        enabled: bool | None = None,
    ) -> bool:
        """Enable or disable fact for consent control."""
        if isinstance(key_or_enabled, bool):
            return self.facts.toggle_by_id(fact_id_or_category, key_or_enabled)
        if enabled is not None:
            if key_or_enabled is not None:
                return self.facts.toggle_fact(fact_id_or_category, str(key_or_enabled), enabled)
            return self.facts.toggle_by_id(fact_id_or_category, enabled)
        return self.facts.toggle_by_id(fact_id_or_category, True)

    def disable_fact(self, fact_id: str) -> bool:
        """Disable a fact by ID for privacy/consent."""
        return self.facts.toggle_by_id(fact_id, enabled=False)

    def enable_fact(self, fact_id: str) -> bool:
        """Enable a fact by ID."""
        return self.facts.toggle_by_id(fact_id, enabled=True)

    def clear_category(self, category: str) -> int:
        """Purge all facts in a category."""
        return self.facts.wipe_category(category)

    def summarize_session(
        self,
        session_id: str,
        messages: list[dict[str, Any]] | None = None,
    ) -> SessionSummary:
        """Trigger post-session background synthesis."""
        return self.summarizer.summarize_session(session_id, messages=messages)

    def export_markdown(self, include_sensitive: bool = False) -> str:
        """Export all facts formatted as markdown."""
        return self.facts.export_markdown(include_sensitive=include_sensitive)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Keyword and semantic search over memory store."""
        return self.retriever.search(query, limit=limit)

    def clear(self) -> int:
        """Privacy wipe: clear all explicit facts, synthesized summaries, and transcripts."""
        count = self.facts.clear_all()
        with self.db.write_transaction() as conn:
            conn.execute("DELETE FROM session_summaries")
            conn.execute("DELETE FROM messages")
        return count

    def close(self) -> None:
        """Close memory database connections."""
        self.db.close()
