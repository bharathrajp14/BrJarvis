"""Asynchronous session synthesis extracting durable facts from transcripts."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .db import Database
from .facts import ExplicitFactStore, FactCategory

logger = logging.getLogger("jarvis.memory.summarizer")


@dataclass(slots=True)
class SessionSummary:
    """Synthesized record of an interactive session and durable facts extracted."""

    session_id: str
    summary_text: str
    durable_facts: list[dict[str, str]] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    turn_count: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SessionSummarizer:
    """Post-session synthesis engine extracting durable context into structured facts."""

    def __init__(self, db: Database, fact_store: ExplicitFactStore | None = None) -> None:
        self.db = db
        self.fact_store = fact_store or ExplicitFactStore(db)

    def record_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        latency_ms: int = 0,
    ) -> None:
        """Record an interactive conversation turn for subsequent background synthesis."""
        now = time.time()
        with self.db.write_transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, correlation_id, current_mode, created_at, updated_at)
                VALUES (?, ?, 'general', ?, ?)
                """,
                (session_id, session_id, now, now),
            )
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, latency_ms, now),
            )

    def extract_durable_facts(self, messages: list[dict[str, Any]] | str) -> list[dict[str, str]]:
        """Heuristically extract durable facts from user turns in transcript."""
        if isinstance(messages, str):
            msgs: list[dict[str, Any]] = [{"role": "user", "content": messages}]
        else:
            msgs = messages

        extracted: list[dict[str, str]] = []

        patterns = [
            # Identity
            (r"\bmy name is ([A-Za-z0-9_\- ]+)", FactCategory.IDENTITY, "name"),
            (r"\bcall me ([A-Za-z0-9_\- ]+)", FactCategory.IDENTITY, "preferred_name"),
            # Preferences
            (r"\bi prefer ([^.,;]+)", FactCategory.PREFERENCE, "preferred_approach"),
            (r"\balways use ([^.,;]+)", FactCategory.PREFERENCE, "preferred_tool"),
            (r"\bi like ([^.,;]+)", FactCategory.PREFERENCE, "like"),
            (r"\bi dislike ([^.,;]+)", FactCategory.PREFERENCE, "dislike"),
            # Projects
            (r"\bworking on ([^.,;]+)", FactCategory.PROJECT, "active_project"),
            (r"\bmy project is ([^.,;]+)", FactCategory.PROJECT, "project_name"),
            (r"\bbuild (project [A-Za-z0-9_\-]+)", FactCategory.PROJECT, "project_name"),
            # Direct remember requests
            (r"\bremember that ([^.,;]+)", FactCategory.CUSTOM, "remembered_fact"),
            (r"\bkeep in mind that ([^.,;]+)", FactCategory.CONSTRAINT, "user_constraint"),
            (r"\bnever use ([^.,;]+)", FactCategory.CONSTRAINT, "forbidden_tool"),
            # Decisions
            (r"\bdecided to ([^.,;]+)", FactCategory.PROJECT, "decision"),
        ]

        for msg in msgs:
            if msg.get("role") != "user":
                continue
            text = str(msg.get("content", "")).strip()

            for regex, category, default_key in patterns:
                match = re.search(regex, text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    if len(val) >= 2 and len(val) <= 120:
                        extracted.append({
                            "category": category.value,
                            "key": default_key,
                            "value": val,
                        })

        return extracted

    def extract_candidate_facts(self, messages: list[dict[str, Any]] | str) -> list[dict[str, str]]:
        """Alias for extract_durable_facts."""
        return self.extract_durable_facts(messages)

    def summarize_session(
        self,
        session_id: str,
        messages: list[dict[str, Any]] | None = None,
        promote_to_facts: bool = True,
    ) -> SessionSummary:
        """Synthesize session transcript and persist durable takeaways."""
        msgs = list(messages or [])
        now = time.time()

        # If messages not supplied, load from database
        if not msgs:
            with self.db.read_connection() as conn:
                rows = conn.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                    (session_id,),
                ).fetchall()
                msgs = [{"role": r["role"], "content": r["content"]} for r in rows]

        turn_count = len(msgs)
        key_points: list[str] = []
        decisions: list[str] = []

        if turn_count == 0:
            summary_text = f"Empty session {session_id} with no recorded turns."
            durable_facts: list[dict[str, str]] = []
        else:
            user_queries = [m["content"] for m in msgs if m.get("role") == "user"]
            first_goal = user_queries[0][:100] if user_queries else "General discussion"
            last_resp = next((m["content"] for m in reversed(msgs) if m.get("role") == "assistant"), "")

            summary_text = (
                f"Session discussed '{first_goal}'. Completed with {turn_count} turns. "
                f"Outcome: {last_resp[:120]}..." if len(last_resp) > 120 else f"Outcome: {last_resp}"
            )
            durable_facts = self.extract_durable_facts(msgs)

            for m in msgs:
                content = str(m.get("content", ""))
                dec_match = re.search(r"\bdecided to ([^.\n]+)", content, re.IGNORECASE)
                if dec_match:
                    decisions.append(dec_match.group(1).strip())
                elif m.get("role") == "user":
                    key_points.append(content[:100])

        # Promote extracted facts into explicit fact store
        if promote_to_facts and durable_facts:
            for item in durable_facts:
                try:
                    self.fact_store.set_fact(
                        category=item["category"],
                        key=item["key"],
                        value=item["value"],
                        source=f"session_synthesis:{session_id}",
                    )
                except Exception as exc:
                    logger.warning("Fact promotion notice: %s", exc)

        facts_json = json.dumps(durable_facts)

        with self.db.write_transaction() as conn:
            conn.execute(
                """
                INSERT INTO session_summaries (
                    session_id, summary_text, durable_facts_extracted, turn_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    summary_text = excluded.summary_text,
                    durable_facts_extracted = excluded.durable_facts_extracted,
                    turn_count = excluded.turn_count,
                    updated_at = excluded.updated_at
                """,
                (session_id, summary_text, facts_json, turn_count, now, now),
            )

        return SessionSummary(
            session_id=session_id,
            summary_text=summary_text,
            durable_facts=durable_facts,
            key_points=key_points,
            decisions=decisions,
            turn_count=turn_count,
            created_at=now,
            updated_at=now,
        )

    def get_summary(self, session_id: str) -> SessionSummary | None:
        """Lookup summary by session ID."""
        with self.db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_summaries WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_summary(row)

    def list_recent_summaries(self, limit: int = 5) -> list[SessionSummary]:
        """Retrieve recent session summaries ordered descending by timestamp."""
        with self.db.read_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM session_summaries ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_summary(r) for r in rows]

    @staticmethod
    def _row_to_summary(row: Any) -> SessionSummary:
        try:
            facts = json.loads(row["durable_facts_extracted"])
        except Exception:
            facts = []
        return SessionSummary(
            session_id=row["session_id"],
            summary_text=row["summary_text"],
            durable_facts=facts,
            turn_count=row["turn_count"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )
