"""Discrete, user-visible, editable, taggable explicit facts store."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .db import Database


class FactCategory(str, Enum):
    """Semantic category for discrete user facts."""

    IDENTITY = "identity"
    PREFERENCE = "preference"
    PROJECT = "project"
    CONSTRAINT = "constraint"
    WORKFLOW = "workflow"
    CUSTOM = "custom"

    @classmethod
    def from_str(cls, val: str) -> FactCategory:
        norm = val.strip().lower()
        for member in cls:
            if member.value == norm or member.name.lower() == norm:
                return member
        return cls.CUSTOM


@dataclass(slots=True)
class ExplicitFact:
    """A discrete, durable, user-visible, and editable memory item."""

    id: str
    category: FactCategory
    key: str
    value: str
    confidence: float = 1.0
    sensitive: bool = False
    enabled: bool = True
    source: str = "user_explicit"
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        return data


class ExplicitFactStore:
    """Authoritative repository for explicit, user-editable facts."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def set_fact(
        self,
        category: str | FactCategory,
        key: str,
        value: str,
        confidence: float = 1.0,
        sensitive: bool = False,
        source: str = "user_explicit",
    ) -> ExplicitFact:
        """Create or update an explicit fact."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        clean_key = key.strip()
        clean_val = value.strip()
        now = time.time()

        with self.db.write_transaction() as conn:
            # Check if exists by (category, key)
            row = conn.execute(
                "SELECT id, created_at, enabled FROM explicit_facts WHERE category = ? AND key = ?",
                (cat_enum.value, clean_key),
            ).fetchone()

            if row is not None:
                fact_id = row["id"]
                created_at = row["created_at"]
                enabled = bool(row["enabled"])
                conn.execute(
                    """
                    UPDATE explicit_facts SET
                        value = ?,
                        confidence = ?,
                        sensitive = ?,
                        source = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (clean_val, confidence, 1 if sensitive else 0, source, now, fact_id),
                )
            else:
                fact_id = f"fact_{uuid.uuid4().hex[:10]}"
                created_at = now
                enabled = True
                conn.execute(
                    """
                    INSERT INTO explicit_facts (
                        id, category, key, value, confidence, sensitive, enabled, source, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fact_id,
                        cat_enum.value,
                        clean_key,
                        clean_val,
                        confidence,
                        1 if sensitive else 0,
                        1,
                        source,
                        now,
                        now,
                    ),
                )

        return ExplicitFact(
            id=fact_id,
            category=cat_enum,
            key=clean_key,
            value=clean_val,
            confidence=confidence,
            sensitive=sensitive,
            enabled=enabled,
            source=source,
            created_at=created_at,
            updated_at=now,
        )

    def get_fact(self, category: str | FactCategory, key: str) -> ExplicitFact | None:
        """Lookup fact by category and key."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        with self.db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM explicit_facts WHERE category = ? AND key = ?",
                (cat_enum.value, key.strip()),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_fact(row)

    def get_fact_by_id(self, fact_id: str) -> ExplicitFact | None:
        """Lookup fact by primary key ID."""
        with self.db.read_connection() as conn:
            row = conn.execute("SELECT * FROM explicit_facts WHERE id = ?", (fact_id.strip(),)).fetchone()
            if row is None:
                return None
            return self._row_to_fact(row)

    def list_facts(
        self,
        category: str | FactCategory | None = None,
        enabled_only: bool = True,
        include_sensitive: bool = True,
        include_disabled: bool | None = None,
    ) -> list[ExplicitFact]:
        """List facts with optional filters."""
        if include_disabled is not None:
            enabled_only = not include_disabled
        query = "SELECT * FROM explicit_facts WHERE 1=1"
        params: list[Any] = []

        if category is not None:
            cat_val = category.value if isinstance(category, FactCategory) else FactCategory.from_str(str(category)).value
            query += " AND category = ?"
            params.append(cat_val)

        if enabled_only:
            query += " AND enabled = 1"

        if not include_sensitive:
            query += " AND sensitive = 0"

        query += " ORDER BY category ASC, key ASC"

        with self.db.read_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def delete_fact(self, category: str | FactCategory, key: str) -> bool:
        """Delete fact by category and key."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        with self.db.write_transaction() as conn:
            cur = conn.execute(
                "DELETE FROM explicit_facts WHERE category = ? AND key = ?",
                (cat_enum.value, key.strip()),
            )
            return cur.rowcount > 0

    def delete_by_id(self, fact_id: str) -> bool:
        """Delete fact by primary key ID."""
        with self.db.write_transaction() as conn:
            cur = conn.execute("DELETE FROM explicit_facts WHERE id = ?", (fact_id.strip(),))
            return cur.rowcount > 0

    def delete_fact_by_id(self, fact_id: str) -> bool:
        """Alias for delete_by_id."""
        return self.delete_by_id(fact_id)

    def delete_by_key(self, key: str) -> bool:
        """Delete fact by key across all categories."""
        with self.db.write_transaction() as conn:
            cur = conn.execute("DELETE FROM explicit_facts WHERE key = ?", (key.strip(),))
            return cur.rowcount > 0

    def toggle_fact(self, category: str | FactCategory, key: str, enabled: bool) -> bool:
        """Enable or disable a fact for consent control without deletion."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        with self.db.write_transaction() as conn:
            cur = conn.execute(
                "UPDATE explicit_facts SET enabled = ?, updated_at = ? WHERE category = ? AND key = ?",
                (1 if enabled else 0, time.time(), cat_enum.value, key.strip()),
            )
            return cur.rowcount > 0

    def toggle_by_id(self, fact_id: str, enabled: bool) -> bool:
        """Enable or disable a fact by ID for UI consent toggles."""
        with self.db.write_transaction() as conn:
            cur = conn.execute(
                "UPDATE explicit_facts SET enabled = ?, updated_at = ? WHERE id = ?",
                (1 if enabled else 0, time.time(), fact_id.strip()),
            )
            return cur.rowcount > 0

    def search_facts(self, query: str, limit: int = 10, enabled_only: bool = True) -> list[ExplicitFact]:
        """Perform tokenized keyword search over keys and values."""
        clean_q = query.strip().lower()
        if not clean_q:
            return self.list_facts(enabled_only=enabled_only)[:limit]

        tokens = [t for t in clean_q.split() if len(t) >= 2]
        if not tokens:
            tokens = [clean_q]

        sql = "SELECT * FROM explicit_facts WHERE ("
        conds = []
        params: list[Any] = []
        for t in tokens:
            conds.append("(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)")
            pat = f"%{t}%"
            params.extend([pat, pat])
        sql += " OR ".join(conds) + ")"

        if enabled_only:
            sql += " AND enabled = 1"

        sql += f" LIMIT {limit}"

        with self.db.read_connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def export_markdown(self, include_sensitive: bool = False) -> str:
        """Export all facts formatted as clean markdown document."""
        facts = self.list_facts(enabled_only=False, include_sensitive=include_sensitive)
        if not facts:
            return "# Persistent User Memory\n\nNo facts currently stored."

        lines = ["# Persistent User Memory", ""]
        by_cat: dict[str, list[ExplicitFact]] = {}
        for f in facts:
            by_cat.setdefault(f.category.value.title(), []).append(f)

        for cat_name, cat_facts in sorted(by_cat.items()):
            lines.append(f"## {cat_name}")
            for f in cat_facts:
                status_badge = "" if f.enabled else " _(disabled)_"
                sens_badge = " [sensitive]" if f.sensitive else ""
                lines.append(f"- **{f.key}**: {f.value}{sens_badge}{status_badge}")
            lines.append("")

        return "\n".join(lines).strip()

    def import_legacy_dict(self, data: dict[str, Any]) -> int:
        """Import from legacy long_term.json structure."""
        count = 0
        cat_map = {
            "identity": FactCategory.IDENTITY,
            "preferences": FactCategory.PREFERENCE,
            "projects": FactCategory.PROJECT,
            "relationships": FactCategory.CUSTOM,
            "wishes": FactCategory.CUSTOM,
            "notes": FactCategory.CUSTOM,
            "monitors": FactCategory.WORKFLOW,
        }

        for top_key, val in data.items():
            if top_key in cat_map and isinstance(val, dict):
                target_cat = cat_map[top_key]
                for k, v in val.items():
                    if isinstance(v, (str, int, float, bool)):
                        self.set_fact(target_cat, k, str(v), source="legacy_import")
                        count += 1
                    elif isinstance(v, dict):
                        for sub_k, sub_v in v.items():
                            self.set_fact(target_cat, f"{k}.{sub_k}", str(sub_v), source="legacy_import")
                            count += 1

        return count

    def import_from_dict(
        self,
        data: dict[str, Any],
        category: str | FactCategory = FactCategory.CUSTOM,
    ) -> int:
        """Import flat key-value dictionary into specified fact category."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        count = 0
        for k, v in data.items():
            self.set_fact(cat_enum, str(k), str(v), source="dict_import")
            count += 1
        return count

    def wipe_category(self, category: str | FactCategory) -> int:
        """Purge all facts within a specific category."""
        cat_enum = category if isinstance(category, FactCategory) else FactCategory.from_str(str(category))
        with self.db.write_transaction() as conn:
            cur = conn.execute("DELETE FROM explicit_facts WHERE category = ?", (cat_enum.value,))
            return cur.rowcount

    def clear_all(self) -> int:
        """Purge all facts (user privacy / wipe action)."""
        with self.db.write_transaction() as conn:
            cur = conn.execute("DELETE FROM explicit_facts")
            return cur.rowcount

    @staticmethod
    def _row_to_fact(row: Any) -> ExplicitFact:
        return ExplicitFact(
            id=row["id"],
            category=FactCategory.from_str(row["category"]),
            key=row["key"],
            value=row["value"],
            confidence=float(row["confidence"]),
            sensitive=bool(row["sensitive"]),
            enabled=bool(row["enabled"]),
            source=row["source"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )
