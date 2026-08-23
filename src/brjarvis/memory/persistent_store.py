# memory/persistent_store.py — Extended Persistent Storage for JARVIS MK37
"""
File-based persistent memory storage with user-level and project-level scopes.
Ported & enhanced for JARVIS MK37.

Storage layout:
  user scope    : ~/.jarvis/memory/<slug>.md
  project scope : .jarvis/memory/<slug>.md  (relative to cwd)

MEMORY.md in each directory is the index file — rebuilt automatically after
every save/delete.

Synchronizes across:
  - Flat Markdown Files with YAML Frontmatter
  - SQLite Relational Database (`memory.db`)
  - ChromaDB / TF-IDF Vector Embeddings
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

USER_MEMORY_DIR = Path.home() / ".jarvis" / "memory"
INDEX_FILENAME = "MEMORY.md"

MAX_INDEX_LINES = 200
MAX_INDEX_BYTES = 25_000


def get_project_memory_dir() -> Path:
    """Return the project-local memory directory (relative to cwd)."""
    return Path.cwd() / ".jarvis" / "memory"


def get_memory_dir(scope: str = "user") -> Path:
    """Return the memory directory for the given scope."""
    if scope == "project":
        return get_project_memory_dir()
    return USER_MEMORY_DIR


# ── Data model ─────────────────────────────────────────────────────────────


class MemoryPersistenceError(RuntimeError):
    """Raised when strict memory persistence cannot complete all configured stores."""


@dataclass
class MemoryEntry:
    """A single memory entry loaded from a .md file or SQLite DB."""

    name: str
    description: str
    type: str  # "user" | "feedback" | "project" | "reference"
    content: str
    file_path: str = ""
    created: str = ""
    scope: str = "user"
    confidence: float = 1.0  # 0.0–1.0; 1.0 = explicit user statement
    source: str = "user"  # "user" | "model" | "tool" | "consolidator"
    last_used_at: str = ""
    conflict_group: str = ""


# ── Helpers ────────────────────────────────────────────────────────────────


def _slugify(name: str) -> str:
    """Convert name to a filesystem-safe slug (max 60 chars)."""
    s = name.lower().strip().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s[:60]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse ---\nkey: value\n---\nbody format."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta, parts[2].strip()


def _format_entry_md(entry: MemoryEntry) -> str:
    """Render a MemoryEntry as a markdown file with YAML frontmatter."""
    lines = [
        "---",
        f"name: {entry.name}",
        f"description: {entry.description}",
        f"type: {entry.type}",
        f"created: {entry.created}",
    ]
    if entry.confidence != 1.0:
        lines.append(f"confidence: {entry.confidence:.2f}")
    if entry.source and entry.source != "user":
        lines.append(f"source: {entry.source}")
    if entry.last_used_at:
        lines.append(f"last_used_at: {entry.last_used_at}")
    if entry.conflict_group:
        lines.append(f"conflict_group: {entry.conflict_group}")
    lines.append("---")
    lines.append(entry.content)
    return "\n".join(lines) + "\n"


# ── SQLite Database Setup ──────────────────────────────────────────────────


def _get_sqlite_conn(scope: str = "user") -> sqlite3.Connection:
    db_dir = get_memory_dir(scope)
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "memory.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            description TEXT,
            type TEXT,
            content TEXT,
            created TEXT,
            scope TEXT,
            confidence REAL,
            source TEXT,
            last_used_at TEXT,
            conflict_group TEXT,
            file_path TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_name ON memories(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            timestamp TEXT,
            content TEXT,
            description TEXT
        )
    """)
    conn.commit()
    return conn


def _backup_version(file_path: Path):
    """Save a historical version of the file before overwrite."""
    try:
        if not file_path.exists():
            return
        history_dir = file_path.parent / ".history"
        history_dir.mkdir(exist_ok=True)
        mtime = file_path.stat().st_mtime
        from datetime import datetime as dt

        timestamp = dt.fromtimestamp(mtime).strftime("%Y%m%d_%H%M%S")
        history_file = history_dir / f"{file_path.stem}_{timestamp}.md"
        history_file.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as e:
        logger.debug("Suppressed exception: %s", e)


# ── Core storage operations ────────────────────────────────────────────────


def save_memory(entry: MemoryEntry, scope: str = "user", *, strict: bool = False) -> None:
    """Write/update a memory file, backup previous version, sync to SQLite/Vector, and rebuild index."""
    from brjarvis.memory.memory_types import redact_secrets

    entry.content = redact_secrets(entry.content)
    entry.description = redact_secrets(entry.description)

    mem_dir = get_memory_dir(scope)
    mem_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(entry.name)
    fp = mem_dir / f"{slug}.md"

    # Versioning: backup existing markdown file
    _backup_version(fp)

    fp.write_text(_format_entry_md(entry), encoding="utf-8")
    entry.file_path = str(fp)
    entry.scope = scope
    _rewrite_index(scope)
    try:
        _sync_to_vector(entry)
    except Exception as e:
        logger.warning("Vector memory sync incomplete for %s/%s: %s", scope, entry.name, e)
        if strict:
            raise MemoryPersistenceError(
                f"Vector memory persistence did not complete for '{entry.name}' in scope '{scope}'"
            ) from e

    # Sync to SQLite

    def _do_sqlite_write():
        conn = _get_sqlite_conn(scope)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT content, description FROM memories WHERE name = ?", (entry.name,))
            row = cursor.fetchone()
            if row:
                from datetime import datetime as dt

                conn.execute(
                    "INSERT INTO memory_versions (name, timestamp, content, description) VALUES (?, ?, ?, ?)",
                    (entry.name, dt.now().isoformat(), row[0], row[1]),
                )

            conn.execute(
                """
                INSERT OR REPLACE INTO memories 
                (id, name, description, type, content, created, scope, confidence, source, last_used_at, conflict_group, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slug,
                    entry.name,
                    entry.description,
                    entry.type,
                    entry.content,
                    entry.created,
                    scope,
                    entry.confidence,
                    entry.source,
                    entry.last_used_at,
                    entry.conflict_group,
                    entry.file_path,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    try:
        from brjarvis.memory.sqlite_lock import run_sqlite_write

        run_sqlite_write(_do_sqlite_write)
        # Also sync to central canonical DB
        from brjarvis.memory.canonical_db import get_canonical_db

        with get_canonical_db().get_connection() as cdb:
            cdb.execute(
                """
                INSERT OR REPLACE INTO persistent_memories (name, type, description, content, scope, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.name,
                    entry.type,
                    entry.description,
                    entry.content,
                    scope,
                    entry.conflict_group,
                    entry.created,
                    time.time(),
                ),
            )
    except Exception as e:
        logger.warning("Memory sync incomplete for %s/%s: %s", scope, entry.name, e)
        if strict:
            raise MemoryPersistenceError(
                f"Memory persistence did not complete for '{entry.name}' in scope '{scope}'"
            ) from e
    _SEARCH_CACHE.clear()


def delete_memory(name: str, scope: str = "user") -> bool:
    """Remove a memory and return whether a persisted file existed."""
    _SEARCH_CACHE.clear()
    mem_dir = get_memory_dir(scope)
    slug = _slugify(name)
    fp = mem_dir / f"{slug}.md"
    existed = fp.exists()
    if existed:
        _backup_version(fp)
        fp.unlink()
    _rewrite_index(scope)
    _remove_from_vector(name)

    # Delete from SQLite
    def _do_sqlite_delete():
        conn = _get_sqlite_conn(scope)
        try:
            conn.execute("DELETE FROM memories WHERE name = ?", (name,))
            conn.commit()
        finally:
            conn.close()

    try:
        from brjarvis.memory.sqlite_lock import run_sqlite_write

        run_sqlite_write(_do_sqlite_delete)
        # Also delete from central canonical DB
        from brjarvis.memory.canonical_db import get_canonical_db

        with get_canonical_db().get_connection() as cdb:
            cdb.execute("DELETE FROM persistent_memories WHERE name = ?", (name,))
            cdb.commit()
    except Exception as e:
        logger.debug("Suppressed exception in memory delete: %s", e)
    return existed


def load_entries(scope: str = "user") -> list[MemoryEntry]:
    """Scan all .md files (except MEMORY.md) in a scope and return entries."""
    mem_dir = get_memory_dir(scope)
    if not mem_dir.exists():
        return []
    entries: list[MemoryEntry] = []
    for fp in sorted(mem_dir.glob("*.md")):
        if fp.name == INDEX_FILENAME:
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        meta, body = parse_frontmatter(text)
        entries.append(
            MemoryEntry(
                name=meta.get("name", fp.stem),
                description=meta.get("description", ""),
                type=meta.get("type", "user"),
                content=body,
                file_path=str(fp),
                created=meta.get("created", ""),
                scope=scope,
                confidence=float(meta.get("confidence", 1.0)),
                source=meta.get("source", "user"),
                last_used_at=meta.get("last_used_at", ""),
                conflict_group=meta.get("conflict_group", ""),
            )
        )
    return entries


def load_index(scope: str = "all") -> list[MemoryEntry]:
    """Load memory entries from one or both scopes."""
    if scope == "all":
        return load_entries("user") + load_entries("project")
    return load_entries(scope)


_SEARCH_CACHE: dict[str, list[MemoryEntry]] = {}


def search_memory(query: str, scope: str = "all") -> list[MemoryEntry]:
    """Search memories using hybrid vector similarity + keyword matching with exact match priority."""
    cache_key = f"{scope}:{query.strip().lower()}"
    if cache_key in _SEARCH_CACHE:
        return list(_SEARCH_CACHE[cache_key])

    all_entries = load_index(scope)
    if not all_entries:
        return []

    valid_names = {e.name for e in all_entries}

    # Keyword match with stop-word filter & exact phrase prioritization
    q = query.lower().strip()
    stop_words = {
        "what",
        "that",
        "this",
        "user",
        "file",
        "code",
        "with",
        "from",
        "have",
        "make",
        "find",
        "show",
        "tell",
        "about",
        "your",
        "some",
        "here",
        "there",
        "then",
        "when",
        "where",
        "which",
        "will",
        "would",
        "could",
        "should",
        "please",
    }
    q_words = [w for w in re.findall(r"\b\w+\b", q) if (len(w) >= 3 or w.isdigit()) and w not in stop_words]
    if not q_words and (len(q) >= 3 or q.isdigit()):
        q_words = [q]

    scored_results: list[tuple[float, MemoryEntry]] = []
    seen_names = set()

    for entry in all_entries:
        haystack = f"{entry.name} {entry.description} {entry.content}".lower()
        if q in haystack:
            scored_results.append((100.0, entry))
            seen_names.add(entry.name)
            continue
        matches = 0
        for w in q_words:
            stem = w.rstrip("s").rstrip("ing").rstrip("tion").rstrip("ed")
            if (len(w) >= 3 and w in haystack) or (len(stem) >= 3 and stem in haystack):
                matches += 1
        if matches > 0:
            scored_results.append((float(matches), entry))
            seen_names.add(entry.name)

    # Attempt vector search
    try:
        vector_results = _vector_search(query, all_entries, top_k=10)
        vector_results = [e for e in vector_results if e.name in valid_names]
        for e in vector_results:
            if e.name not in seen_names:
                scored_results.append((5.0, e))
                seen_names.add(e.name)
    except Exception:
        pass

    # Sort by match score descending
    scored_results.sort(key=lambda x: x[0], reverse=True)
    res = [entry for score, entry in scored_results]
    _SEARCH_CACHE[cache_key] = res
    return res


# ── Optional ChromaDB vector layer ─────────────────────────────────────────

_chroma_collection = None
_chroma_available = False

try:
    import chromadb  # type: ignore

    _chroma_available = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


def _get_chroma_collection():
    """Lazy-load ChromaDB collection."""
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
    if not _chroma_available:
        return None
    try:
        db_path = str(USER_MEMORY_DIR / ".chromadb")
        client = chromadb.PersistentClient(path=db_path)
        _chroma_collection = client.get_or_create_collection(name="jarvis_memory", metadata={"hnsw:space": "cosine"})
        return _chroma_collection
    except Exception:
        return None


def _sync_to_vector(entry: MemoryEntry):
    """Add/update a memory entry in the vector store."""
    coll = _get_chroma_collection()
    if coll is None:
        return
    try:
        doc_text = f"{entry.name} {entry.description} {entry.content}"
        coll.upsert(
            ids=[_slugify(entry.name)],
            documents=[doc_text],
            metadatas=[
                {
                    "name": entry.name,
                    "type": entry.type,
                    "scope": entry.scope,
                    "source": entry.source,
                    "confidence": str(entry.confidence),
                }
            ],
        )
    except Exception as e:
        logger.debug("Suppressed exception: %s", e)


def _remove_from_vector(name: str):
    """Remove a memory from the vector store."""
    coll = _get_chroma_collection()
    if coll is None:
        return
    try:
        coll.delete(ids=[_slugify(name)])
    except Exception as e:
        logger.debug("Suppressed exception: %s", e)


def _vector_search(query: str, all_entries: list[MemoryEntry], top_k: int = 10) -> list[MemoryEntry]:
    """Search using ChromaDB vector similarity."""
    coll = _get_chroma_collection()
    if coll is None:
        return []
    try:
        count = coll.count()
        if count == 0:
            for e in all_entries:
                _sync_to_vector(e)
            count = coll.count()
        if count == 0:
            return []
        results = coll.query(query_texts=[query], n_results=min(top_k, count))
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        entry_map = {_slugify(e.name): e for e in all_entries}
        matched = []
        if "distances" in results and results["distances"] and results["distances"][0]:
            for slug, dist in zip(results["ids"][0], results["distances"][0]):
                if dist <= 0.45:  # ⚡ Strict cosine distance cutoff (0=identical, <0.45=relevant)
                    if slug in entry_map:
                        matched.append(entry_map[slug])
        else:
            for slug in results["ids"][0]:
                if slug in entry_map:
                    matched.append(entry_map[slug])
        return matched
    except Exception:
        return []


def _rewrite_index(scope: str) -> None:
    """Rebuild MEMORY.md for the given scope from all .md files in that dir."""
    mem_dir = get_memory_dir(scope)
    if not mem_dir.exists():
        return
    index_path = mem_dir / INDEX_FILENAME
    entries = load_entries(scope)
    lines = [f"- [{e.name}]({Path(e.file_path).name}) — {e.description}" for e in entries]
    index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def get_index_content(scope: str = "user") -> str:
    """Return raw MEMORY.md content for the given scope, or '' if absent."""
    mem_dir = get_memory_dir(scope)
    index_path = mem_dir / INDEX_FILENAME
    if not index_path.exists():
        return ""
    return index_path.read_text(encoding="utf-8").strip()


def check_conflict(entry: MemoryEntry, scope: str = "user") -> dict | None:
    """Check whether a same-named memory already exists with different content."""
    mem_dir = get_memory_dir(scope)
    slug = _slugify(entry.name)
    fp = mem_dir / f"{slug}.md"
    if not fp.exists():
        return None
    try:
        meta, existing_content = parse_frontmatter(fp.read_text(encoding="utf-8"))
    except Exception:
        return None
    if existing_content.strip() == entry.content.strip():
        return None
    return {
        "existing_content": existing_content.strip(),
        "existing_confidence": float(meta.get("confidence", 1.0)),
        "existing_created": meta.get("created", ""),
        "existing_source": meta.get("source", "user"),
    }


def touch_last_used(file_path: str) -> None:
    """Update the last_used_at frontmatter field of a memory file to today."""
    from datetime import date

    fp = Path(file_path)
    if not fp.exists():
        return
    try:
        text = fp.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        today = date.today().isoformat()
        if meta.get("last_used_at") == today:
            return
        meta["last_used_at"] = today
        fm_lines = ["---"]
        for k in ("name", "description", "type", "created", "confidence", "source", "last_used_at", "conflict_group"):
            v = meta.get(k)
            if v is not None and str(v):
                fm_lines.append(f"{k}: {v}")
        fm_lines.append("---")
        new_text = "\n".join(fm_lines) + "\n" + body + "\n"
        fp.write_text(new_text, encoding="utf-8")
    except Exception as e:
        logger.debug("Suppressed exception: %s", e)
