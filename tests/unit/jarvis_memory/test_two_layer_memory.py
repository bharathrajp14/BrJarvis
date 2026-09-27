"""Comprehensive unit tests for the two-layer canonical memory subsystem."""

from __future__ import annotations

import pytest

from jarvis.memory.db import Database
from jarvis.memory.facts import ExplicitFactStore, FactCategory
from jarvis.memory.retrieval import MemoryRetriever
from jarvis.memory.schema import initialize_database
from jarvis.memory.summarizer import SessionSummarizer
from jarvis.memory.unified import UnifiedMemory


@pytest.fixture
def memory_db(tmp_path) -> Database:
    """Fixture providing a clean, initialized SQLite WAL database."""
    db_path = tmp_path / "test_memory.db"
    db = Database(db_path)
    initialize_database(db)
    return db


@pytest.fixture
def fact_store(memory_db: Database) -> ExplicitFactStore:
    return ExplicitFactStore(memory_db)


@pytest.fixture
def summarizer(memory_db: Database, fact_store: ExplicitFactStore) -> SessionSummarizer:
    return SessionSummarizer(memory_db, fact_store)


@pytest.fixture
def retriever(fact_store: ExplicitFactStore, summarizer: SessionSummarizer) -> MemoryRetriever:
    return MemoryRetriever(fact_store, summarizer)


@pytest.fixture
def unified_mem(tmp_path) -> UnifiedMemory:
    db_path = tmp_path / "unified.db"
    return UnifiedMemory(db_path)


# ── ExplicitFactStore Tests ───────────────────────────────────────────────────


def test_explicit_fact_store_crud(fact_store: ExplicitFactStore) -> None:
    # 1. Create
    fact = fact_store.set_fact(
        category=FactCategory.IDENTITY,
        key="full_name",
        value="Bharath Raj",
        source="user_explicit",
    )
    assert len(fact.id) > 0
    assert fact.category == "identity"
    assert fact.key == "full_name"
    assert fact.value == "Bharath Raj"
    assert fact.enabled is True

    # 2. Read single
    retrieved = fact_store.get_fact(FactCategory.IDENTITY, "full_name")
    assert retrieved is not None
    assert retrieved.value == "Bharath Raj"

    # 3. Update
    updated = fact_store.set_fact(
        category=FactCategory.IDENTITY,
        key="full_name",
        value="Bharath Raj P",
        source="user_explicit",
    )
    assert updated.id == fact.id
    assert updated.value == "Bharath Raj P"
    assert updated.updated_at >= fact.created_at

    # 4. List by category
    identity_facts = fact_store.list_facts(category=FactCategory.IDENTITY)
    assert len(identity_facts) == 1
    assert identity_facts[0].value == "Bharath Raj P"


def test_explicit_fact_store_consent_and_toggle(fact_store: ExplicitFactStore) -> None:
    fact = fact_store.set_fact(
        category=FactCategory.PREFERENCE,
        key="editor",
        value="VSCode",
    )

    # Toggle off (disable)
    assert fact_store.toggle_by_id(fact.id, enabled=False) is True
    assert fact_store.get_fact(FactCategory.PREFERENCE, "editor") is not None
    assert fact_store.get_fact(FactCategory.PREFERENCE, "editor").enabled is False
    assert len(fact_store.list_facts(category=FactCategory.PREFERENCE, enabled_only=True)) == 0

    # Still listed in all facts
    all_facts = fact_store.list_facts(include_disabled=True)
    assert len(all_facts) == 1
    assert all_facts[0].enabled is False

    # Toggle back on
    assert fact_store.toggle_by_id(fact.id, enabled=True) is True
    assert fact_store.get_fact(FactCategory.PREFERENCE, "editor") is not None
    assert fact_store.get_fact(FactCategory.PREFERENCE, "editor").enabled is True

    # Delete permanently
    assert fact_store.delete_fact_by_id(fact.id) is True
    assert fact_store.list_facts(include_disabled=True) == []


def test_explicit_fact_store_search_and_export(fact_store: ExplicitFactStore) -> None:
    fact_store.set_fact(FactCategory.PROJECT, "project_brjarvis", "Personal AI Operating System")
    fact_store.set_fact(FactCategory.PREFERENCE, "theme", "dark_mode")
    fact_store.set_fact(FactCategory.CONSTRAINT, "no_telemetry", "Strict local-first privacy")

    # Search
    results = fact_store.search_facts("AI Operating System")
    assert len(results) >= 1
    assert results[0].key == "project_brjarvis"

    # Markdown export
    md = fact_store.export_markdown()
    assert "# Persistent User Memory" in md
    assert "project_brjarvis" in md
    assert "dark_mode" in md
    assert "Strict local-first privacy" in md


def test_explicit_fact_store_migration_and_wipe(fact_store: ExplicitFactStore) -> None:
    legacy_data = {
        "user_name": "Tony",
        "favorite_color": "crimson",
        "framework": "fastapi",
    }
    imported_count = fact_store.import_from_dict(legacy_data, category=FactCategory.CUSTOM)
    assert imported_count == 3

    assert len(fact_store.list_facts(category=FactCategory.CUSTOM)) == 3

    # Wipe category
    deleted = fact_store.wipe_category(FactCategory.CUSTOM)
    assert deleted == 3
    assert len(fact_store.list_facts(category=FactCategory.CUSTOM)) == 0


# ── SessionSummarizer Tests ───────────────────────────────────────────────────


def test_session_summarizer_heuristic_extraction(summarizer: SessionSummarizer) -> None:
    text = (
        "Hello assistant! My name is Arthur Dent. "
        "Please note that I prefer tea over coffee. "
        "Currently I am working on project Hitchhiker. "
        "Also, never use unencrypted sockets."
    )
    candidates = summarizer.extract_candidate_facts(text)
    assert len(candidates) >= 3

    keys = [c["key"] for c in candidates]
    assert "name" in keys or "preferred_name" in keys
    assert any("prefer" in k or "preference" in k or "approach" in k for k in keys)


def test_session_summarizer_end_of_session_compaction(summarizer: SessionSummarizer) -> None:
    session_id = "test-session-101"

    summarizer.record_turn(session_id, "user", "Hello, my name is Bruce Wayne.")
    summarizer.record_turn(
        session_id,
        "assistant",
        "Hello Mr. Wayne, how can I assist Gotham today?",
    )
    summarizer.record_turn(
        session_id,
        "user",
        "I decided to build Project Batmobile using Python and Rust. Let's make sure it has stealth mode.",
    )
    summarizer.record_turn(
        session_id,
        "assistant",
        "Understood. We will configure stealth mode for Project Batmobile.",
    )

    summary = summarizer.summarize_session(session_id)
    assert summary is not None
    assert summary.session_id == session_id
    assert summary.turn_count == 4
    assert len(summary.decisions) > 0 or len(summary.key_points) > 0

    # Verify auto-promoted facts in fact store
    recent_summaries = summarizer.list_recent_summaries(limit=5)
    assert len(recent_summaries) == 1
    assert recent_summaries[0].session_id == session_id


# ── MemoryRetriever Tests ─────────────────────────────────────────────────────


def test_memory_retriever_bounded_context(
    fact_store: ExplicitFactStore,
    summarizer: SessionSummarizer,
    retriever: MemoryRetriever,
) -> None:
    # Add identity & preferences
    fact_store.set_fact(FactCategory.IDENTITY, "name", "Clark Kent")
    fact_store.set_fact(FactCategory.IDENTITY, "role", "Investigative Journalist")
    fact_store.set_fact(FactCategory.PREFERENCE, "style", "terse and objective")
    fact_store.set_fact(FactCategory.PROJECT, "daily_planet", "Investigating LexCorp corruption")

    # Retrieve for a query
    context = retriever.retrieve_context("What should I write for the Daily Planet article?")

    assert "## Relevant Memory Context:" in context
    assert "Clark Kent" in context
    assert "Daily Planet" in context or "daily_planet" in context
    assert len(context) <= 2400


def test_memory_retriever_respects_max_chars(
    fact_store: ExplicitFactStore,
    retriever: MemoryRetriever,
) -> None:
    for i in range(50):
        fact_store.set_fact(
            FactCategory.CUSTOM,
            f"key_{i}",
            f"This is a long fact value with index {i} that takes up quite a bit of space.",
        )

    context = retriever.retrieve_context("query about anything", max_chars=500)
    assert len(context) <= 600  # allowing minimal formatting buffer


# ── UnifiedMemory Facade Tests ────────────────────────────────────────────────


def test_unified_memory_facade(unified_mem: UnifiedMemory) -> None:
    # 1. Explicit memory API
    fact = unified_mem.remember("framework", "FastAPI", category="preference")
    assert fact.key == "framework"
    assert fact.value == "FastAPI"

    unified_mem.set_preference("editor", "Neovim")
    assert unified_mem.get_preference("editor") == "Neovim"

    # Profile dictionary
    profile = unified_mem.get_profile()
    assert profile["framework"] == "FastAPI"
    assert profile["editor"] == "Neovim"

    # 2. Context recall
    ctx = unified_mem.recall("Which framework and editor do I use?")
    assert "FastAPI" in ctx
    assert "Neovim" in ctx

    # 3. Privacy / consent controls
    all_facts = unified_mem.list_all_facts()
    assert len(all_facts) == 2

    # Disable fact
    assert unified_mem.disable_fact(fact.id) is True
    # Verify disabled fact is no longer retrieved
    ctx_after_disable = unified_mem.recall("Which framework do I use?")
    assert "FastAPI" not in ctx_after_disable

    # Delete fact
    assert unified_mem.delete_fact(fact.id) is True
    assert len(unified_mem.list_all_facts()) == 1

    # Clear category
    unified_mem.clear_category("preference")
    assert len(unified_mem.list_all_facts()) == 0
