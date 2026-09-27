"""Point-in-time temporal facts engine tracking attribute truth over time."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .db import Database


@dataclass(slots=True)
class FactRecord:
    """Represents a fact verified at a specific point in time."""

    entity: str
    attribute: str
    value: str
    confidence: float
    valid_from: float
    valid_to: float | None
    source: str
    id: int = 0


class TemporalEngine:
    """Manages mutable entity-attribute values with historical audit trails."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def record_fact(
        self,
        entity: str,
        attribute: str,
        value: str,
        confidence: float = 1.0,
        source: str = "system",
    ) -> FactRecord:
        """Record an updated fact, retiring any previous truth for this entity/attribute."""
        now = time.time()
        with self.db.write_transaction() as conn:
            # Invalidate previous active fact
            conn.execute(
                """
                UPDATE temporal_facts
                SET valid_to = ?
                WHERE entity = ? AND attribute = ? AND valid_to IS NULL
                """,
                (now, entity, attribute),
            )

            # Insert new fact
            cursor = conn.execute(
                """
                INSERT INTO temporal_facts (
                    entity, attribute, value, confidence, valid_from, valid_to, source, created_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (entity, attribute, value, confidence, now, source, now),
            )
            fact_id = cursor.lastrowid or 0

            return FactRecord(
                id=fact_id,
                entity=entity,
                attribute=attribute,
                value=value,
                confidence=confidence,
                valid_from=now,
                valid_to=None,
                source=source,
            )

    def get_current_truth(self, entity: str, attribute: str) -> FactRecord | None:
        """Retrieve the currently active truth for an entity and attribute."""
        with self.db.read_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM temporal_facts
                WHERE entity = ? AND attribute = ? AND valid_to IS NULL
                ORDER BY id DESC LIMIT 1
                """,
                (entity, attribute),
            ).fetchone()

            if row is None:
                return None

            return FactRecord(
                id=row["id"],
                entity=row["entity"],
                attribute=row["attribute"],
                value=row["value"],
                confidence=row["confidence"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                source=row["source"],
            )

    def get_history(self, entity: str, attribute: str) -> list[FactRecord]:
        """Retrieve chronological history of all values for an entity and attribute."""
        with self.db.read_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM temporal_facts
                WHERE entity = ? AND attribute = ?
                ORDER BY valid_from ASC
                """,
                (entity, attribute),
            ).fetchall()

            return [
                FactRecord(
                    id=r["id"],
                    entity=r["entity"],
                    attribute=r["attribute"],
                    value=r["value"],
                    confidence=r["confidence"],
                    valid_from=r["valid_from"],
                    valid_to=r["valid_to"],
                    source=r["source"],
                )
                for r in rows
            ]
