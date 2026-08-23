# memory/workspace_store.py — Unified Workspace Data Store for BR JARVIS MK40.2 / MK41
"""
Authoritative Data Access Store for BR JARVIS Workspace Entities:
- Projects & Project Files
- Conversations, Branches & Messages
- Artifacts & Provenance Tracking
- System & Task Notifications
- Unified Full-Text Search (FTS5)
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from brjarvis.memory.canonical_db import CanonicalDatabaseManager, get_canonical_db

logger = logging.getLogger("JARVIS.WorkspaceStore")


@dataclass
class ProjectRecord:
    project_id: str
    name: str
    description: str = ""
    instructions: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    pinned: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "settings": self.settings,
            "pinned": bool(self.pinned),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ProjectFileRecord:
    file_id: str
    project_id: str
    filename: str
    file_path: str
    file_size: int = 0
    mime_type: str = "application/octet-stream"
    file_hash: str = ""
    status: str = "READY"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationRecord:
    conversation_id: str
    title: str
    project_id: Optional[str] = None
    pinned: bool = False
    archived: bool = False
    active_branch_id: str = "main"
    summary: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "project_id": self.project_id,
            "pinned": bool(self.pinned),
            "archived": bool(self.archived),
            "active_branch_id": self.active_branch_id,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MessageRecord:
    message_id: str
    conversation_id: str
    role: str
    content: str
    branch_id: str = "main"
    parent_message_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    linked_task_id: Optional[str] = None
    linked_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    backend: str = "gemini"
    latency_ms: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "branch_id": self.branch_id,
            "parent_message_id": self.parent_message_id,
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "linked_task_id": self.linked_task_id,
            "linked_artifacts": self.linked_artifacts,
            "backend": self.backend,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }


@dataclass
class ArtifactItem:
    artifact_id: str
    filename: str
    host_path: str
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    message_id: Optional[str] = None
    sandbox_path: Optional[str] = None
    mime_type: str = "application/octet-stream"
    file_size: int = 0
    sha256: str = ""
    version: int = 1
    provider: str = "jarvis"
    verification_status: str = "PENDING"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationRecord:
    notification_id: str
    title: str
    message: str
    category: str = "ALL"
    severity: str = "info"
    is_read: bool = False
    action_link: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "is_read": bool(self.is_read),
            "action_link": self.action_link,
            "data": self.data,
            "created_at": self.created_at,
        }


class WorkspaceStore:
    """Canonical Workspace Data Store connecting all runtime entities."""

    def __init__(self, db_manager: Optional[CanonicalDatabaseManager] = None):
        self.db = db_manager or get_canonical_db()

    def _index_fts(self, entity_type: str, entity_id: str, title: str, content: str, project_id: Optional[str] = None):
        """Index or update full-text search entry."""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "DELETE FROM workspace_fts WHERE entity_type = ? AND entity_id = ?",
                    (entity_type, entity_id),
                )
                conn.execute(
                    "INSERT INTO workspace_fts (entity_type, entity_id, title, content, project_id) VALUES (?, ?, ?, ?, ?)",
                    (entity_type, entity_id, title[:200], content[:10000], project_id or ""),
                )
                conn.commit()
        except Exception as e:
            logger.debug("FTS index error (non-fatal): %s", e)

    # ── Projects ─────────────────────────────────────────────────────────────

    def create_project(
        self,
        name: str,
        description: str = "",
        instructions: str = "",
        settings: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> ProjectRecord:
        pid = project_id or f"proj_{uuid.uuid4().hex[:10]}"
        now = time.time()
        settings_str = json.dumps(settings or {})

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, description, instructions, settings_json, pinned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (pid, name, description, instructions, settings_str, now, now),
            )
            conn.commit()

        self._index_fts("project", pid, name, f"{description} {instructions}", pid)
        return ProjectRecord(
            project_id=pid,
            name=name,
            description=description,
            instructions=instructions,
            settings=settings or {},
            pinned=False,
            created_at=now,
            updated_at=now,
        )

    def get_project(self, project_id: str) -> Optional[ProjectRecord]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
            if not row:
                return None
            try:
                st = json.loads(row["settings_json"] or "{}")
            except Exception:
                st = {}
            return ProjectRecord(
                project_id=row["project_id"],
                name=row["name"],
                description=row["description"] or "",
                instructions=row["instructions"] or "",
                settings=st,
                pinned=bool(row["pinned"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_projects(self) -> List[ProjectRecord]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY pinned DESC, updated_at DESC").fetchall()
            results = []
            for r in rows:
                try:
                    st = json.loads(r["settings_json"] or "{}")
                except Exception:
                    st = {}
                results.append(
                    ProjectRecord(
                        project_id=r["project_id"],
                        name=r["name"],
                        description=r["description"] or "",
                        instructions=r["instructions"] or "",
                        settings=st,
                        pinned=bool(r["pinned"]),
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                )
            return results

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        pinned: Optional[bool] = None,
    ) -> Optional[ProjectRecord]:
        proj = self.get_project(project_id)
        if not proj:
            return None

        new_name = name if name is not None else proj.name
        new_desc = description if description is not None else proj.description
        new_inst = instructions if instructions is not None else proj.instructions
        new_sett = settings if settings is not None else proj.settings
        new_pinned = int(pinned) if pinned is not None else int(proj.pinned)
        now = time.time()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE projects
                SET name = ?, description = ?, instructions = ?, settings_json = ?, pinned = ?, updated_at = ?
                WHERE project_id = ?
                """,
                (new_name, new_desc, new_inst, json.dumps(new_sett), new_pinned, now, project_id),
            )
            conn.commit()

        self._index_fts("project", project_id, new_name, f"{new_desc} {new_inst}", project_id)
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            conn.commit()
            return cur.rowcount > 0

    # ── Project Files ────────────────────────────────────────────────────────

    def add_project_file(
        self,
        project_id: str,
        filename: str,
        file_path: str,
        file_size: int = 0,
        mime_type: str = "application/octet-stream",
        file_hash: str = "",
        status: str = "READY",
    ) -> ProjectFileRecord:
        fid = f"file_{uuid.uuid4().hex[:10]}"
        now = time.time()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_files (file_id, project_id, filename, file_path, file_size, mime_type, file_hash, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (fid, project_id, filename, file_path, file_size, mime_type, file_hash, status, now, now),
            )
            conn.commit()

        self._index_fts("file", fid, filename, f"{filename} {file_path}", project_id)
        return ProjectFileRecord(
            file_id=fid,
            project_id=project_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            status=status,
            created_at=now,
            updated_at=now,
        )

    def list_project_files(self, project_id: str) -> List[ProjectFileRecord]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM project_files WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
            return [
                ProjectFileRecord(
                    file_id=r["file_id"],
                    project_id=r["project_id"],
                    filename=r["filename"],
                    file_path=r["file_path"],
                    file_size=r["file_size"] or 0,
                    mime_type=r["mime_type"] or "application/octet-stream",
                    file_hash=r["file_hash"] or "",
                    status=r["status"] or "READY",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def get_project_file(self, project_id: str, file_id: str) -> Optional[ProjectFileRecord]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_files WHERE project_id = ? AND file_id = ?",
                (project_id, file_id),
            ).fetchone()
            if not row:
                return None
            return ProjectFileRecord(
                file_id=row["file_id"],
                project_id=row["project_id"],
                filename=row["filename"],
                file_path=row["file_path"],
                file_size=row["file_size"] or 0,
                mime_type=row["mime_type"] or "application/octet-stream",
                file_hash=row["file_hash"] or "",
                status=row["status"] or "READY",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_project_file(self, file_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.execute("DELETE FROM project_files WHERE file_id = ?", (file_id,))
            conn.commit()
            return cur.rowcount > 0

    # ── Conversations ────────────────────────────────────────────────────────

    def create_conversation(
        self,
        title: str = "New Chat",
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ConversationRecord:
        cid = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        main_branch_id = f"br_main_{cid}"
        now = time.time()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (conversation_id, project_id, title, pinned, archived, active_branch_id, summary, created_at, updated_at)
                VALUES (?, ?, ?, 0, 0, ?, '', ?, ?)
                """,
                (cid, project_id, title, main_branch_id, now, now),
            )
            # Create default main branch
            conn.execute(
                """
                INSERT INTO conversation_branches (branch_id, conversation_id, parent_message_id, name, created_at)
                VALUES (?, ?, NULL, 'Main Branch', ?)
                """,
                (main_branch_id, cid, now),
            )
            conn.commit()

        self._index_fts("conversation", cid, title, title, project_id)
        return ConversationRecord(
            conversation_id=cid,
            title=title,
            project_id=project_id,
            pinned=False,
            archived=False,
            active_branch_id=main_branch_id,
            summary="",
            created_at=now,
            updated_at=now,
        )

    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if not row:
                return None
            return ConversationRecord(
                conversation_id=row["conversation_id"],
                title=row["title"],
                project_id=row["project_id"],
                pinned=bool(row["pinned"]),
                archived=bool(row["archived"]),
                active_branch_id=row["active_branch_id"] or "main",
                summary=row["summary"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_conversations(
        self,
        project_id: Optional[str] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[ConversationRecord]:
        with self.db.get_connection() as conn:
            query = "SELECT * FROM conversations WHERE 1=1"
            params: List[Any] = []

            if not include_archived:
                query += " AND archived = 0"
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if search:
                query += " AND (title LIKE ? OR summary LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            query += " ORDER BY pinned DESC, updated_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, tuple(params)).fetchall()
            return [
                ConversationRecord(
                    conversation_id=r["conversation_id"],
                    title=r["title"],
                    project_id=r["project_id"],
                    pinned=bool(r["pinned"]),
                    archived=bool(r["archived"]),
                    active_branch_id=r["active_branch_id"] or "main",
                    summary=r["summary"] or "",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
        pinned: Optional[bool] = None,
        archived: Optional[bool] = None,
        active_branch_id: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[ConversationRecord]:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None

        new_title = title if title is not None else conv.title
        new_proj = project_id if project_id is not None else conv.project_id
        new_pinned = int(pinned) if pinned is not None else int(conv.pinned)
        new_arch = int(archived) if archived is not None else int(conv.archived)
        new_branch = active_branch_id if active_branch_id is not None else conv.active_branch_id
        new_summary = summary if summary is not None else conv.summary
        now = time.time()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE conversations
                SET title = ?, project_id = ?, pinned = ?, archived = ?, active_branch_id = ?, summary = ?, updated_at = ?
                WHERE conversation_id = ?
                """,
                (new_title, new_proj, new_pinned, new_arch, new_branch, new_summary, now, conversation_id),
            )
            conn.commit()

        self._index_fts("conversation", conversation_id, new_title, f"{new_title} {new_summary}", new_proj)
        return self.get_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            conn.commit()
            return cur.rowcount > 0

    def branch_conversation(
        self,
        conversation_id: str,
        parent_message_id: str,
        branch_name: Optional[str] = None,
    ) -> str:
        """Create a new conversational branch from an earlier message."""
        branch_id = f"br_{uuid.uuid4().hex[:8]}"
        name = branch_name or f"Branch {branch_id}"
        now = time.time()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_branches (branch_id, conversation_id, parent_message_id, name, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (branch_id, conversation_id, parent_message_id, name, now),
            )
            conn.execute(
                "UPDATE conversations SET active_branch_id = ?, updated_at = ? WHERE conversation_id = ?",
                (branch_id, now, conversation_id),
            )
            conn.commit()

        return branch_id

    def duplicate_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        """Duplicate an existing conversation and its messages into a new conversation."""
        src = self.get_conversation(conversation_id)
        if not src:
            return None

        new_conv = self.create_conversation(
            title=f"{src.title} (Copy)",
            project_id=src.project_id,
        )

        messages = self.get_messages(conversation_id)
        for msg in messages:
            self.add_message(
                conversation_id=new_conv.conversation_id,
                role=msg.role,
                content=msg.content,
                branch_id="main",
                tool_calls=msg.tool_calls,
                linked_task_id=msg.linked_task_id,
                linked_artifacts=msg.linked_artifacts,
                backend=msg.backend,
            )

        return new_conv

    # ── Messages ─────────────────────────────────────────────────────────────

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        branch_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        linked_task_id: Optional[str] = None,
        linked_artifacts: Optional[List[Dict[str, Any]]] = None,
        backend: str = "gemini",
        latency_ms: int = 0,
        message_id: Optional[str] = None,
    ) -> MessageRecord:
        mid = message_id or f"msg_{uuid.uuid4().hex[:12]}"
        now = time.time()
        tc_json = json.dumps(tool_calls or [])
        art_json = json.dumps(linked_artifacts or [])

        conv = self.get_conversation(conversation_id)
        actual_branch = branch_id or (conv.active_branch_id if conv else "main")

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (message_id, conversation_id, branch_id, parent_message_id, role, content, tool_calls_json, linked_task_id, linked_artifacts_json, backend, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mid,
                    conversation_id,
                    actual_branch,
                    parent_message_id,
                    role,
                    content,
                    tc_json,
                    linked_task_id,
                    art_json,
                    backend,
                    latency_ms,
                    now,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now, conversation_id),
            )
            conn.commit()

        # FTS index for user and assistant messages
        proj_id = conv.project_id if conv else None
        self._index_fts(
            "message", mid, f"{role.upper()} in {conv.title if conv else conversation_id}", content, proj_id
        )

        # Auto-title conversation on first meaningful user message if title is default
        if role.lower() == "user" and conv and conv.title in ("New Chat", "New Conversation"):
            auto_title = self.generate_title(content)
            if auto_title:
                self.update_conversation(conversation_id, title=auto_title)

        return MessageRecord(
            message_id=mid,
            conversation_id=conversation_id,
            branch_id=actual_branch,
            parent_message_id=parent_message_id,
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            linked_task_id=linked_task_id,
            linked_artifacts=linked_artifacts or [],
            backend=backend,
            latency_ms=latency_ms,
            created_at=now,
        )

    def get_messages(self, conversation_id: str, branch_id: Optional[str] = None) -> List[MessageRecord]:
        with self.db.get_connection() as conn:
            if branch_id:
                rows = conn.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? AND (branch_id = ? OR branch_id = 'main') ORDER BY created_at ASC",
                    (conversation_id, branch_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                    (conversation_id,),
                ).fetchall()

            messages = []
            for r in rows:
                try:
                    tc = json.loads(r["tool_calls_json"] or "[]")
                except Exception:
                    tc = []
                try:
                    art = json.loads(r["linked_artifacts_json"] or "[]")
                except Exception:
                    art = []
                messages.append(
                    MessageRecord(
                        message_id=r["message_id"],
                        conversation_id=r["conversation_id"],
                        branch_id=r["branch_id"] or "main",
                        parent_message_id=r["parent_message_id"],
                        role=r["role"],
                        content=r["content"] or "",
                        tool_calls=tc,
                        linked_task_id=r["linked_task_id"],
                        linked_artifacts=art,
                        backend=r["backend"] or "gemini",
                        latency_ms=r["latency_ms"] or 0,
                        created_at=r["created_at"],
                    )
                )
            return messages

    @staticmethod
    def generate_title(first_prompt: str) -> str:
        """Derive a concise, content-aware title from the initial prompt."""
        text = re.sub(r"[\r\n\t]+", " ", first_prompt).strip()
        # Clean common prefixes
        text = re.sub(
            r"^(please|can you|help me|jarvis|hey jarvis|i want to|create a|build a|write a)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        )
        words = text.split()
        if not words:
            return "Conversation"
        title_cand = " ".join(words[:6]).capitalize()
        if len(title_cand) > 40:
            title_cand = title_cand[:37] + "..."
        return title_cand

    # ── Artifacts ────────────────────────────────────────────────────────────

    def record_artifact(
        self,
        filename: str,
        host_path: str,
        conversation_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        message_id: Optional[str] = None,
        sandbox_path: Optional[str] = None,
        mime_type: str = "application/octet-stream",
        file_size: int = 0,
        sha256: str = "",
        version: int = 1,
        provider: str = "jarvis",
        verification_status: str = "PENDING",
        artifact_id: Optional[str] = None,
    ) -> ArtifactItem:
        aid = artifact_id or f"art_{uuid.uuid4().hex[:12]}"
        now = time.time()

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (artifact_id, conversation_id, task_id, project_id, message_id, filename, host_path, sandbox_path, mime_type, file_size, sha256, version, provider, verification_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    conversation_id,
                    task_id,
                    project_id,
                    message_id,
                    filename,
                    host_path,
                    sandbox_path,
                    mime_type,
                    file_size,
                    sha256,
                    version,
                    provider,
                    verification_status,
                    now,
                ),
            )
            conn.commit()

        self._index_fts("artifact", aid, filename, f"{filename} {host_path}", project_id)
        return ArtifactItem(
            artifact_id=aid,
            conversation_id=conversation_id,
            task_id=task_id,
            project_id=project_id,
            message_id=message_id,
            filename=filename,
            host_path=host_path,
            sandbox_path=sandbox_path,
            mime_type=mime_type,
            file_size=file_size,
            sha256=sha256,
            version=version,
            provider=provider,
            verification_status=verification_status,
            created_at=now,
        )

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactItem]:
        with self.db.get_connection() as conn:
            r = conn.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
            if not r:
                return None
            return ArtifactItem(
                artifact_id=r["artifact_id"],
                conversation_id=r["conversation_id"],
                task_id=r["task_id"],
                project_id=r["project_id"],
                message_id=r["message_id"],
                filename=r["filename"],
                host_path=r["host_path"],
                sandbox_path=r["sandbox_path"],
                mime_type=r["mime_type"] or "application/octet-stream",
                file_size=r["file_size"] or 0,
                sha256=r["sha256"] or "",
                version=r["version"] or 1,
                provider=r["provider"] or "jarvis",
                verification_status=r["verification_status"] or "PENDING",
                created_at=r["created_at"],
            )

    def list_artifacts(
        self,
        conversation_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ArtifactItem]:
        with self.db.get_connection() as conn:
            query = "SELECT * FROM artifacts WHERE 1=1"
            params: List[Any] = []

            if conversation_id:
                query += " AND conversation_id = ?"
                params.append(conversation_id)
            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, tuple(params)).fetchall()
            return [
                ArtifactItem(
                    artifact_id=r["artifact_id"],
                    conversation_id=r["conversation_id"],
                    task_id=r["task_id"],
                    project_id=r["project_id"],
                    message_id=r["message_id"],
                    filename=r["filename"],
                    host_path=r["host_path"],
                    sandbox_path=r["sandbox_path"],
                    mime_type=r["mime_type"] or "application/octet-stream",
                    file_size=r["file_size"] or 0,
                    sha256=r["sha256"] or "",
                    version=r["version"] or 1,
                    provider=r["provider"] or "jarvis",
                    verification_status=r["verification_status"] or "PENDING",
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def verify_artifact(self, artifact_id: str, verified: bool = True) -> bool:
        st = "VERIFIED" if verified else "FAILED"
        with self.db.get_connection() as conn:
            cur = conn.execute("UPDATE artifacts SET verification_status = ? WHERE artifact_id = ?", (st, artifact_id))
            conn.commit()
            return cur.rowcount > 0

    # ── Notifications ────────────────────────────────────────────────────────

    def add_notification(
        self,
        title: str,
        message: str,
        category: str = "ALL",
        severity: str = "info",
        action_link: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> NotificationRecord:
        nid = f"notif_{uuid.uuid4().hex[:10]}"
        now = time.time()
        data_str = json.dumps(data or {})

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notifications (notification_id, title, message, category, severity, is_read, action_link, data_json, created_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (nid, title, message, category.upper(), severity, action_link, data_str, now),
            )
            conn.commit()

        return NotificationRecord(
            notification_id=nid,
            title=title,
            message=message,
            category=category.upper(),
            severity=severity,
            is_read=False,
            action_link=action_link,
            data=data or {},
            created_at=now,
        )

    def list_notifications(
        self, category: Optional[str] = None, unread_only: bool = False, limit: int = 50
    ) -> List[NotificationRecord]:
        with self.db.get_connection() as conn:
            query = "SELECT * FROM notifications WHERE 1=1"
            params: List[Any] = []

            if category and category.upper() != "ALL":
                query += " AND category = ?"
                params.append(category.upper())
            if unread_only:
                query += " AND is_read = 0"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, tuple(params)).fetchall()
            results = []
            for r in rows:
                try:
                    dt = json.loads(r["data_json"] or "{}")
                except Exception:
                    dt = {}
                results.append(
                    NotificationRecord(
                        notification_id=r["notification_id"],
                        title=r["title"],
                        message=r["message"],
                        category=r["category"] or "ALL",
                        severity=r["severity"] or "info",
                        is_read=bool(r["is_read"]),
                        action_link=r["action_link"],
                        data=dt,
                        created_at=r["created_at"],
                    )
                )
            return results

    def mark_notification_read(self, notification_id: str) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.execute("UPDATE notifications SET is_read = 1 WHERE notification_id = ?", (notification_id,))
            conn.commit()
            return cur.rowcount > 0

    def mark_all_notifications_read(self) -> int:
        with self.db.get_connection() as conn:
            cur = conn.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
            conn.commit()
            return cur.rowcount

    # ── Global Unified Search ────────────────────────────────────────────────

    def search_all(self, query_str: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Search across all entity types (conversations, messages, projects, tasks, artifacts, files)."""
        if not query_str or not query_str.strip():
            return []

        clean_q = query_str.strip()
        results: List[Dict[str, Any]] = []

        with self.db.get_connection() as conn:
            # 1. Try FTS5 search
            try:
                fts_rows = conn.execute(
                    """
                    SELECT entity_type, entity_id, title, snippet(workspace_fts, 3, '<b>', '</b>', '...', 15) AS snippet
                    FROM workspace_fts
                    WHERE workspace_fts MATCH ?
                    LIMIT ?
                    """,
                    (f"{clean_q}*", limit),
                ).fetchall()
                for r in fts_rows:
                    results.append(
                        {
                            "entity_type": r["entity_type"],
                            "entity_id": r["entity_id"],
                            "title": r["title"],
                            "snippet": r["snippet"] or "",
                        }
                    )
            except Exception:
                pass

            # 2. Fallback SQL LIKE if FTS had no matches or errored
            if len(results) < 5:
                # Search conversations
                conv_rows = conn.execute(
                    "SELECT conversation_id, title FROM conversations WHERE title LIKE ? LIMIT 10",
                    (f"%{clean_q}%",),
                ).fetchall()
                for c in conv_rows:
                    if not any(r["entity_id"] == c["conversation_id"] for r in results):
                        results.append(
                            {
                                "entity_type": "conversation",
                                "entity_id": c["conversation_id"],
                                "title": c["title"],
                                "snippet": f"Conversation: {c['title']}",
                            }
                        )

                # Search projects
                proj_rows = conn.execute(
                    "SELECT project_id, name, description FROM projects WHERE name LIKE ? OR description LIKE ? LIMIT 5",
                    (f"%{clean_q}%", f"%{clean_q}%"),
                ).fetchall()
                for p in proj_rows:
                    if not any(r["entity_id"] == p["project_id"] for r in results):
                        results.append(
                            {
                                "entity_type": "project",
                                "entity_id": p["project_id"],
                                "title": p["name"],
                                "snippet": p["description"] or "Project Workspace",
                            }
                        )

                # Search artifacts
                art_rows = conn.execute(
                    "SELECT artifact_id, filename, host_path FROM artifacts WHERE filename LIKE ? LIMIT 5",
                    (f"%{clean_q}%",),
                ).fetchall()
                for a in art_rows:
                    if not any(r["entity_id"] == a["artifact_id"] for r in results):
                        results.append(
                            {
                                "entity_type": "artifact",
                                "entity_id": a["artifact_id"],
                                "title": a["filename"],
                                "snippet": a["host_path"] or "Artifact File",
                            }
                        )

                # Search tasks
                task_rows = conn.execute(
                    "SELECT task_id, goal, status FROM tasks WHERE goal LIKE ? LIMIT 5",
                    (f"%{clean_q}%",),
                ).fetchall()
                for t in task_rows:
                    if not any(r["entity_id"] == t["task_id"] for r in results):
                        results.append(
                            {
                                "entity_type": "task",
                                "entity_id": t["task_id"],
                                "title": t["goal"],
                                "snippet": f"Task ({t['status']}): {t['goal']}",
                            }
                        )

        return results[:limit]


_GLOBAL_WORKSPACE_STORE: Optional[WorkspaceStore] = None


def get_workspace_store() -> WorkspaceStore:
    """Return singleton WorkspaceStore instance."""
    global _GLOBAL_WORKSPACE_STORE
    if _GLOBAL_WORKSPACE_STORE is None:
        _GLOBAL_WORKSPACE_STORE = WorkspaceStore()
    return _GLOBAL_WORKSPACE_STORE
