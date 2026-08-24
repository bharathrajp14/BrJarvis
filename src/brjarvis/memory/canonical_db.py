# memory/canonical_db.py — Unified Canonical SQLite WAL Store & Connection Manager
"""
Central Database Manager for BR JARVIS.
Consolidates system state into a unified, high-concurrency SQLite database operating in WAL mode.
Authoritative Single Source of Truth for:
- canonical_memories (28-field temporal memory model)
- tasks & task_steps & checkpoints
- decisions & decision_receipts
- execution_ledger
- experience_trajectories & lessons
- contacts & devices & routines
- workspace projects, conversations, messages, artifacts
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from brjarvis.core.paths import paths

logger = logging.getLogger("JARVIS.CanonicalDB")

_CANONICAL_DIR = paths.PROJECT_ROOT / ".jarvis"
CANONICAL_DB_PATH = _CANONICAL_DIR / "jarvis_canonical.db"


class CanonicalDatabaseManager:
    """Thread-safe SQLite connection manager with WAL mode and auto-migrations."""

    def __init__(self, db_path: Path = CANONICAL_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a connection with WAL mode and busy timeout."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize and migrate all canonical tables."""
        with self._lock:
            with self.get_connection() as conn:
                # 1. Canonical Memories (28-field authoritative schema)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS canonical_memories (
                        memory_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'default_user',
                        project_id TEXT NOT NULL DEFAULT 'global',
                        scope TEXT NOT NULL DEFAULT 'user',
                        namespace TEXT NOT NULL DEFAULT 'default',
                        memory_type TEXT NOT NULL,
                        entity TEXT,
                        attribute TEXT,
                        value TEXT,
                        content TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_id TEXT,
                        evidence TEXT,
                        confidence REAL DEFAULT 1.0,
                        reliability REAL DEFAULT 1.0,
                        importance REAL DEFAULT 0.5,
                        created_at REAL NOT NULL,
                        observed_at REAL NOT NULL,
                        effective_from REAL NOT NULL,
                        effective_until REAL,
                        updated_at REAL NOT NULL,
                        last_accessed_at REAL NOT NULL,
                        last_validated_at REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'ACTIVE',
                        version INTEGER DEFAULT 1,
                        supersedes_memory_id TEXT,
                        superseded_by_memory_id TEXT,
                        conflict_group_id TEXT,
                        session_id TEXT,
                        task_id TEXT,
                        decision_id TEXT,
                        tags_json TEXT DEFAULT '[]',
                        content_hash TEXT,
                        embedding_id TEXT,
                        retention_class TEXT NOT NULL DEFAULT 'NORMAL'
                    )
                """)
                existing_cols = self._get_columns(conn, "canonical_memories")
                if "retention_class" not in existing_cols:
                    try:
                        conn.execute("ALTER TABLE canonical_memories ADD COLUMN retention_class TEXT DEFAULT 'NORMAL'")
                        conn.commit()
                    except Exception as _col_err:
                        logger.debug("retention_class migration notice: %s", _col_err)

                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_cm_user_proj_scope ON canonical_memories(user_id, project_id, scope);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_cm_status_effective ON canonical_memories(status, effective_from, effective_until);"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cm_type ON canonical_memories(memory_type);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cm_entity_attr ON canonical_memories(entity, attribute);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cm_conflict ON canonical_memories(conflict_group_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cm_hash ON canonical_memories(content_hash);")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_cm_retention ON canonical_memories(retention_class, effective_until);"
                )

                # 2. Legacy Persistent Memories Compatibility Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS persistent_memories (
                        name TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        description TEXT,
                        content TEXT NOT NULL,
                        scope TEXT DEFAULT 'user',
                        tags TEXT,
                        created_at TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)

                # 3. Preferences Store
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        scope TEXT DEFAULT 'user',
                        updated_at REAL NOT NULL
                    )
                """)

                # 4. Tasks & Step Checkpoints
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        goal TEXT NOT NULL,
                        status TEXT NOT NULL,
                        current_step INTEGER DEFAULT 0,
                        total_steps INTEGER DEFAULT 0,
                        active_agents TEXT,
                        active_devices TEXT,
                        data_json TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        revision INTEGER NOT NULL DEFAULT 0
                    )
                """)
                task_columns = self._get_columns(conn, "tasks")
                if "revision" not in task_columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN revision INTEGER NOT NULL DEFAULT 0")
                    conn.commit()
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_steps (
                        step_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        step_index INTEGER NOT NULL,
                        capability TEXT NOT NULL,
                        parameters_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        result_json TEXT,
                        error_msg TEXT,
                        verified INTEGER DEFAULT 0,
                        duration REAL DEFAULT 0.0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        step_index INTEGER NOT NULL,
                        state_snapshot TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    )
                """)

                # 5. Decisions & Decision Receipts
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS decisions (
                        decision_id TEXT PRIMARY KEY,
                        task_id TEXT,
                        question TEXT NOT NULL,
                        goal TEXT NOT NULL,
                        options_json TEXT NOT NULL,
                        selected_option TEXT NOT NULL,
                        rejected_options_json TEXT NOT NULL,
                        evidence TEXT,
                        constraints_json TEXT,
                        risk_level TEXT DEFAULT 'low',
                        confidence REAL DEFAULT 1.0,
                        expected_outcome TEXT,
                        verification_plan TEXT,
                        reversible INTEGER DEFAULT 1,
                        approval_required INTEGER DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'ACTIVE',
                        actual_outcome TEXT,
                        receipt_json TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_task ON decisions(task_id);")

                # 6. Append-Only Execution Ledger
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS execution_ledger_entries (
                        execution_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        step_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        arguments_hash TEXT NOT NULL,
                        parameters_json TEXT NOT NULL,
                        result_preview TEXT,
                        stdout TEXT,
                        stderr TEXT,
                        return_code INTEGER DEFAULT 0,
                        duration_seconds REAL DEFAULT 0.0,
                        side_effects_json TEXT DEFAULT '[]',
                        evidence TEXT,
                        verification_status TEXT NOT NULL,
                        error TEXT,
                        timestamp REAL NOT NULL
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_ledger_task_step ON execution_ledger_entries(task_id, step_id);"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_tool ON execution_ledger_entries(tool_name);")

                # 7. Learned Lessons & Experience Trajectories
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS lessons (
                        lesson_id TEXT PRIMARY KEY,
                        topic TEXT NOT NULL,
                        rule TEXT NOT NULL,
                        reason TEXT,
                        evidence TEXT,
                        scope TEXT DEFAULT 'global',
                        source TEXT DEFAULT 'user',
                        confidence REAL DEFAULT 0.8,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'ACTIVE',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        last_used_at REAL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS experience_trajectories (
                        trajectory_id TEXT PRIMARY KEY,
                        goal_query TEXT NOT NULL,
                        tool_sequence_json TEXT NOT NULL,
                        success_status INTEGER NOT NULL,
                        failure_reason TEXT,
                        execution_context_json TEXT,
                        duration_seconds REAL DEFAULT 0.0,
                        side_effects_json TEXT DEFAULT '[]',
                        timestamp REAL NOT NULL
                    )
                """)

                # 8. Session Lifecycle Records (Non-destructive)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_records (
                        session_id TEXT PRIMARY KEY,
                        start_time REAL NOT NULL,
                        end_time REAL,
                        summary TEXT,
                        goals_json TEXT DEFAULT '[]',
                        decisions_json TEXT DEFAULT '[]',
                        constraints_json TEXT DEFAULT '[]',
                        unfinished_tasks_json TEXT DEFAULT '[]',
                        errors_json TEXT DEFAULT '[]',
                        successful_actions_json TEXT DEFAULT '[]',
                        next_actions_json TEXT DEFAULT '[]',
                        consumed INTEGER DEFAULT 0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)

                # 9. Unified Contacts
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        phone_number TEXT,
                        email TEXT,
                        aliases_json TEXT,
                        notes TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)

                # 10. Background Routines
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS routines (
                        routine_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        goal TEXT NOT NULL,
                        trigger_type TEXT NOT NULL,
                        trigger_config_json TEXT,
                        skill_name TEXT,
                        target_device TEXT DEFAULT 'pc',
                        enabled INTEGER DEFAULT 1,
                        requires_approval INTEGER DEFAULT 0,
                        last_run_at REAL,
                        next_run_at REAL,
                        created_at REAL NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS routine_runs (
                        run_id TEXT PRIMARY KEY,
                        routine_id TEXT NOT NULL,
                        task_id TEXT,
                        status TEXT NOT NULL,
                        result_summary TEXT,
                        duration REAL,
                        executed_at REAL NOT NULL,
                        FOREIGN KEY (routine_id) REFERENCES routines(routine_id) ON DELETE CASCADE
                    )
                """)

                # 11. Paired Devices
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS devices (
                        device_id TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        trust_state TEXT NOT NULL,
                        public_key TEXT,
                        auth_token TEXT,
                        last_seen_at REAL NOT NULL,
                        metadata_json TEXT
                    )
                """)

                # 12. Immutable Audit Trail
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id TEXT PRIMARY KEY,
                        correlation_id TEXT,
                        task_id TEXT,
                        timestamp REAL NOT NULL,
                        event_type TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        action TEXT NOT NULL,
                        target_resource TEXT,
                        risk_level TEXT,
                        decision TEXT,
                        details_json TEXT
                    )
                """)

                # 13. Workspace Projects, Files, Conversations, Messages, Artifacts
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        instructions TEXT DEFAULT '',
                        settings_json TEXT DEFAULT '{}',
                        pinned INTEGER DEFAULT 0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS project_files (
                        file_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER DEFAULT 0,
                        mime_type TEXT DEFAULT 'application/octet-stream',
                        file_hash TEXT DEFAULT '',
                        status TEXT DEFAULT 'READY',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        project_id TEXT,
                        title TEXT NOT NULL,
                        pinned INTEGER DEFAULT 0,
                        archived INTEGER DEFAULT 0,
                        active_branch_id TEXT DEFAULT 'main',
                        summary TEXT DEFAULT '',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_branches (
                        branch_id TEXT NOT NULL,
                        conversation_id TEXT NOT NULL,
                        parent_message_id TEXT,
                        name TEXT NOT NULL DEFAULT 'Main Branch',
                        created_at REAL NOT NULL,
                        PRIMARY KEY (conversation_id, branch_id),
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        branch_id TEXT DEFAULT 'main',
                        parent_message_id TEXT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL DEFAULT '',
                        tool_calls_json TEXT DEFAULT '[]',
                        linked_task_id TEXT,
                        linked_artifacts_json TEXT DEFAULT '[]',
                        backend TEXT DEFAULT 'gemini',
                        latency_ms INTEGER DEFAULT 0,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS artifacts (
                        artifact_id TEXT PRIMARY KEY,
                        conversation_id TEXT,
                        task_id TEXT,
                        project_id TEXT,
                        message_id TEXT,
                        filename TEXT NOT NULL,
                        host_path TEXT NOT NULL,
                        sandbox_path TEXT,
                        mime_type TEXT DEFAULT 'application/octet-stream',
                        file_size INTEGER DEFAULT 0,
                        sha256 TEXT DEFAULT '',
                        version INTEGER DEFAULT 1,
                        provider TEXT DEFAULT 'jarvis',
                        verification_status TEXT DEFAULT 'PENDING',
                        created_at REAL NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE SET NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        notification_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        category TEXT DEFAULT 'ALL',
                        severity TEXT DEFAULT 'info',
                        is_read INTEGER DEFAULT 0,
                        action_link TEXT,
                        data_json TEXT DEFAULT '{}',
                        created_at REAL NOT NULL
                    )
                """)

                # 14. Workspace FTS5 Virtual Table
                try:
                    conn.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS workspace_fts USING fts5(
                            entity_type,
                            entity_id,
                            title,
                            content,
                            project_id,
                            tokenize='porter unicode61'
                        );
                    """)
                except Exception as _fts_err:
                    logger.debug("FTS5 table setup notice: %s", _fts_err)

                # 15. Handoffs (cross-session & cross-agent continuation objects)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS handoffs (
                        handoff_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        project_id TEXT DEFAULT 'global',
                        source_agent TEXT DEFAULT 'jarvis',
                        target_agent TEXT DEFAULT '',
                        created_at REAL NOT NULL,
                        expires_at REAL,
                        goal TEXT NOT NULL DEFAULT '',
                        completed_json TEXT DEFAULT '[]',
                        current_state TEXT DEFAULT '',
                        failed_attempts_json TEXT DEFAULT '[]',
                        decisions_json TEXT DEFAULT '[]',
                        open_questions_json TEXT DEFAULT '[]',
                        next_steps_json TEXT DEFAULT '[]',
                        important_files_json TEXT DEFAULT '[]',
                        risks_json TEXT DEFAULT '[]',
                        confidence REAL DEFAULT 1.0,
                        status TEXT DEFAULT 'OPEN',
                        reusable INTEGER DEFAULT 0,
                        claimed_by TEXT DEFAULT '',
                        claimed_at REAL,
                        delivered_at REAL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_handoffs_session ON handoffs(session_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_handoffs_status ON handoffs(status);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_handoffs_project ON handoffs(project_id, status);")

                # 16. Memory Feedback (retrieval quality tuning)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        memory_id TEXT NOT NULL,
                        session_id TEXT DEFAULT '',
                        query TEXT DEFAULT '',
                        signal TEXT NOT NULL,
                        note TEXT DEFAULT '',
                        created_at REAL NOT NULL,
                        FOREIGN KEY (memory_id) REFERENCES canonical_memories(memory_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_memory ON memory_feedback(memory_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_signal ON memory_feedback(signal);")

                # 17. Sessions (authoritative stateful session persistence)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'default_user',
                        agent_id TEXT NOT NULL DEFAULT 'jarvis-general',
                        device_id TEXT NOT NULL DEFAULT 'pc_primary',
                        project_id TEXT NOT NULL DEFAULT 'global',
                        workspace_id TEXT NOT NULL DEFAULT 'default',
                        active_task_id TEXT,
                        current_state TEXT NOT NULL DEFAULT 'NEW',
                        active_model TEXT NOT NULL DEFAULT 'gemini',
                        permission_mode TEXT NOT NULL DEFAULT 'confirm_destructive',
                        current_mode TEXT NOT NULL DEFAULT 'general',
                        event_sequence INTEGER DEFAULT 0,
                        data_json TEXT NOT NULL DEFAULT '{}',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_proj ON sessions(user_id, project_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(current_state);")

                # 18. Session Checkpoints (durable state recovery and rollback snapshots)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        turn_index INTEGER NOT NULL DEFAULT 0,
                        active_task_id TEXT,
                        snapshot_json TEXT NOT NULL DEFAULT '{}',
                        created_at REAL NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_ckpt_sess ON session_checkpoints(session_id);")

                conn.commit()

    @staticmethod
    def _get_columns(conn: sqlite3.Connection, table: str) -> set:
        """Return set of column names for an existing table (used for safe migrations)."""
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            return {row["name"] for row in cursor.fetchall()}
        except Exception:
            return set()

    # ── Preferences API ────────────────────────────────────────────────────────

    def set_preference(self, key: str, value: str, scope: str = "user") -> None:
        """Store or update a user/system preference."""
        with self._lock:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO preferences (key, value, scope, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                    """,
                    (key, str(value), scope, time.time()),
                )
                conn.commit()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a preference value by key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default

    # ── Sessions & Session Checkpoints Persistence API ────────────────────────

    def save_session_record(self, session_data: Dict[str, Any]) -> None:
        """Persist or update a canonical session record in SQLite WAL database."""
        with self._lock:
            with self.get_connection() as conn:
                session_id = session_data.get("session_id", "")
                user_id = session_data.get("user_id", "default_user")
                agent_id = session_data.get("agent_id", "jarvis-general")
                device_id = session_data.get("device_id", "pc_primary")
                project_id = session_data.get("project_id", "global")
                workspace_id = session_data.get("workspace_id", "default")
                active_task_id = session_data.get("active_task_id")
                current_state = session_data.get("current_state", "ACTIVE")
                if hasattr(current_state, "value"):
                    current_state = current_state.value
                active_model = session_data.get("active_model", "gemini")
                permission_mode = session_data.get("permission_mode", "confirm_destructive")
                current_mode = session_data.get("current_mode", "general")
                event_sequence = int(session_data.get("event_sequence", 0))
                data_json = json.dumps(session_data)
                now = time.time()
                created_at = float(session_data.get("created_at", now))
                updated_at = float(session_data.get("updated_at", now))

                conn.execute(
                    """
                    INSERT INTO sessions (
                        session_id, user_id, agent_id, device_id, project_id, workspace_id,
                        active_task_id, current_state, active_model, permission_mode,
                        current_mode, event_sequence, data_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        user_id = excluded.user_id,
                        agent_id = excluded.agent_id,
                        device_id = excluded.device_id,
                        project_id = excluded.project_id,
                        workspace_id = excluded.workspace_id,
                        active_task_id = excluded.active_task_id,
                        current_state = excluded.current_state,
                        active_model = excluded.active_model,
                        permission_mode = excluded.permission_mode,
                        current_mode = excluded.current_mode,
                        event_sequence = excluded.event_sequence,
                        data_json = excluded.data_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        session_id,
                        user_id,
                        agent_id,
                        device_id,
                        project_id,
                        workspace_id,
                        active_task_id,
                        str(current_state),
                        active_model,
                        permission_mode,
                        current_mode,
                        event_sequence,
                        data_json,
                        created_at,
                        updated_at,
                    ),
                )
                conn.commit()

    def get_session_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session data dictionary from the canonical database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                return json.loads(row["data_json"])
            except Exception:
                return None

    def list_session_records(self, user_id: str = "default_user", limit: int = 50) -> List[Dict[str, Any]]:
        """List active or recent session records."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data_json FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            )
            results = []
            for row in cursor.fetchall():
                try:
                    results.append(json.loads(row["data_json"]))
                except Exception:
                    pass
            return results

    def delete_session_record(self, session_id: str) -> bool:
        """Delete a session and all its associated checkpoints."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                count = cursor.rowcount
                conn.commit()
                return count > 0

    def save_session_checkpoint_record(self, checkpoint_data: Dict[str, Any]) -> None:
        """Store a session checkpoint snapshot in SQLite WAL database."""
        with self._lock:
            with self.get_connection() as conn:
                ckpt_id = checkpoint_data.get("checkpoint_id", f"ckpt-{uuid.uuid4().hex[:8]}")
                session_id = checkpoint_data.get("session_id", "")
                state = checkpoint_data.get("state", "ACTIVE")
                turn_index = int(checkpoint_data.get("turn_index", 0))
                active_task_id = checkpoint_data.get("active_task_id")
                snapshot_json = json.dumps(checkpoint_data.get("snapshot_data", checkpoint_data))
                created_at = float(checkpoint_data.get("created_at", time.time()))

                conn.execute(
                    """
                    INSERT INTO session_checkpoints (
                        checkpoint_id, session_id, state, turn_index, active_task_id,
                        snapshot_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(checkpoint_id) DO UPDATE SET
                        state = excluded.state,
                        turn_index = excluded.turn_index,
                        active_task_id = excluded.active_task_id,
                        snapshot_json = excluded.snapshot_json
                    """,
                    (ckpt_id, session_id, str(state), turn_index, active_task_id, snapshot_json, created_at),
                )
                conn.commit()

    def get_session_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all checkpoints for a session in chronological order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checkpoint_id, state, turn_index, active_task_id, snapshot_json, created_at FROM session_checkpoints WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            )
            results = []
            for row in cursor.fetchall():
                try:
                    snapshot = json.loads(row["snapshot_json"])
                    results.append(
                        {
                            "checkpoint_id": row["checkpoint_id"],
                            "session_id": session_id,
                            "state": row["state"],
                            "turn_index": row["turn_index"],
                            "active_task_id": row["active_task_id"],
                            "snapshot_data": snapshot,
                            "created_at": row["created_at"],
                        }
                    )
                except Exception:
                    pass
            return results

    # ── Database Maintenance, Integrity & Backups ─────────────────────────────

    def check_integrity(self) -> bool:
        """Run SQLite integrity check."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                res = cursor.fetchall()
                is_ok = len(res) == 1 and res[0][0] == "ok"
                if not is_ok:
                    logger.error("Canonical DB integrity check failed: %s", res)
                return is_ok
        except Exception as e:
            logger.error("Canonical DB integrity check error: %s", e)
            return False

    def create_backup(self, target_path: Optional[Path] = None) -> Path:
        """Create a safe snapshot backup of the canonical database."""
        with self._lock:
            if target_path is None:
                backup_dir = self.db_path.parent / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                target_path = backup_dir / f"canonical_backup_{timestamp}.db"

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with self.get_connection() as src:
                dst = sqlite3.connect(str(target_path))
                try:
                    src.backup(dst)
                finally:
                    dst.close()
            logger.info("Canonical DB snapshot backup created at %s", target_path)
            return target_path


_GLOBAL_CANONICAL_DB: Optional[CanonicalDatabaseManager] = None


def get_canonical_db() -> CanonicalDatabaseManager:
    """Return the singleton canonical database manager."""
    global _GLOBAL_CANONICAL_DB
    if _GLOBAL_CANONICAL_DB is None:
        _GLOBAL_CANONICAL_DB = CanonicalDatabaseManager()
    return _GLOBAL_CANONICAL_DB
