"""Database table schema definitions and idempotent migrations."""

from __future__ import annotations

from .db import Database

MIGRATION_V1 = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    user_request TEXT NOT NULL,
    status TEXT NOT NULL,
    current_step INTEGER NOT NULL DEFAULT 0,
    total_steps INTEGER NOT NULL DEFAULT 0,
    revision INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS task_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    result TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 1,
    timestamp REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS task_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    step INTEGER NOT NULL,
    status TEXT NOT NULL,
    revision INTEGER NOT NULL,
    metadata TEXT NOT NULL,
    timestamp REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    current_mode TEXT NOT NULL DEFAULT 'general',
    active_task_id TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    timestamp REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS temporal_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    valid_from REAL NOT NULL,
    valid_to REAL,
    source TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS explicit_facts (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    sensitive INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,
    source TEXT NOT NULL DEFAULT 'user_explicit',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS session_summaries (
    session_id TEXT PRIMARY KEY,
    summary_text TEXT NOT NULL,
    durable_facts_extracted TEXT NOT NULL DEFAULT '[]',
    turn_count INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    revision INTEGER NOT NULL,
    reason TEXT NOT NULL,
    timestamp REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_temporal_lookup ON temporal_facts(entity, attribute, valid_to);
CREATE INDEX IF NOT EXISTS idx_explicit_facts_lookup ON explicit_facts(category, key, enabled);
CREATE INDEX IF NOT EXISTS idx_explicit_facts_enabled ON explicit_facts(enabled);
CREATE INDEX IF NOT EXISTS idx_session_summaries_time ON session_summaries(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_events ON task_events(task_id, revision);
CREATE INDEX IF NOT EXISTS idx_task_actions ON task_actions(task_id, step);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
"""


def initialize_database(db: Database) -> None:
    """Apply database migrations idempotently."""
    conn = db.connect()
    try:
        conn.executescript(MIGRATION_V1)
    finally:
        conn.close()
