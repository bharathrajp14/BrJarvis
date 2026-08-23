# api/routes/conversations.py — Conversation & Branch Management Endpoints for BR JARVIS MK40.2 / MK41
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from brjarvis.memory.workspace_store import get_workspace_store

logger = logging.getLogger("JARVIS.API.Conversations")
router = APIRouter(tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Chat"
    project_id: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    project_id: Optional[str] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None
    active_branch_id: Optional[str] = None
    summary: Optional[str] = None


class CreateBranchRequest(BaseModel):
    parent_message_id: str
    branch_name: Optional[str] = None


class PostMessageRequest(BaseModel):
    role: str = "user"
    content: str
    branch_id: Optional[str] = "main"
    parent_message_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    linked_task_id: Optional[str] = None
    linked_artifacts: Optional[List[Dict[str, Any]]] = None
    backend: Optional[str] = "gemini"


@router.get("/conversations")
async def list_conversations(
    project_id: Optional[str] = None,
    include_archived: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
):
    """List conversations grouped or filtered by project, archive status, and search."""
    store = get_workspace_store()
    convs = store.list_conversations(
        project_id=project_id,
        include_archived=include_archived,
        search=search,
        limit=limit,
    )
    return {"total": len(convs), "conversations": [c.to_dict() for c in convs]}


@router.post("/conversations")
async def create_conversation(req: CreateConversationRequest):
    """Create a new persistent conversation record."""
    store = get_workspace_store()
    conv = store.create_conversation(
        title=req.title or "New Chat",
        project_id=req.project_id,
    )
    return {"status": "success", "conversation": conv.to_dict()}


@router.get("/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: str):
    """Get full conversation metadata, messages, linked tasks, and artifacts."""
    store = get_workspace_store()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = store.get_messages(conversation_id, branch_id=conv.active_branch_id)
    artifacts = store.list_artifacts(conversation_id=conversation_id)

    return {
        "conversation": conv.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "artifacts": [a.to_dict() for a in artifacts],
    }


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, req: UpdateConversationRequest):
    """Update title, pinned, archived, or project association."""
    store = get_workspace_store()
    updated = store.update_conversation(
        conversation_id=conversation_id,
        title=req.title,
        project_id=req.project_id,
        pinned=req.pinned,
        archived=req.archived,
        active_branch_id=req.active_branch_id,
        summary=req.summary,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "conversation": updated.to_dict()}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Permanently delete a conversation and its messages."""
    store = get_workspace_store()
    success = store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}


@router.post("/conversations/{conversation_id}/branch")
async def branch_conversation(conversation_id: str, req: CreateBranchRequest):
    """Create a conversational branch from an earlier message."""
    store = get_workspace_store()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    branch_id = store.branch_conversation(
        conversation_id=conversation_id,
        parent_message_id=req.parent_message_id,
        branch_name=req.branch_name,
    )
    return {"status": "success", "branch_id": branch_id, "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/duplicate")
async def duplicate_conversation(conversation_id: str):
    """Duplicate an existing conversation with history into a new one."""
    store = get_workspace_store()
    new_conv = store.duplicate_conversation(conversation_id)
    if not new_conv:
        raise HTTPException(status_code=404, detail="Source conversation not found")
    return {"status": "success", "conversation": new_conv.to_dict()}


@router.get("/conversations/{conversation_id}/messages")
async def list_conversation_messages(conversation_id: str, branch_id: Optional[str] = None):
    """Get messages for a conversation, optionally filtered by branch."""
    store = get_workspace_store()
    messages = store.get_messages(conversation_id, branch_id=branch_id)
    return {"total": len(messages), "messages": [m.to_dict() for m in messages]}


@router.post("/conversations/{conversation_id}/messages")
async def add_conversation_message(conversation_id: str, req: PostMessageRequest):
    """Persist a message into the conversation."""
    store = get_workspace_store()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = store.add_message(
        conversation_id=conversation_id,
        role=req.role,
        content=req.content,
        branch_id=req.branch_id or conv.active_branch_id or "main",
        parent_message_id=req.parent_message_id,
        tool_calls=req.tool_calls,
        linked_task_id=req.linked_task_id,
        linked_artifacts=req.linked_artifacts,
        backend=req.backend or "gemini",
    )
    return {"status": "success", "message": msg.to_dict()}


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = Query("markdown", pattern="^(markdown|json|text)$")):
    """Export conversation transcript in Markdown, JSON, or Text."""
    store = get_workspace_store()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = store.get_messages(conversation_id, branch_id=conv.active_branch_id)

    if format == "json":
        return {
            "conversation": conv.to_dict(),
            "messages": [m.to_dict() for m in messages],
        }

    lines = [f"# {conv.title}\n", f"*Exported on {conv.updated_at}*\n\n---\n"]
    for m in messages:
        author = "👤 **User**" if m.role == "user" else "⚡ **JARVIS**"
        lines.append(f"### {author}\n{m.content}\n\n")

    md_content = "\n".join(lines)
    return {"format": "markdown", "filename": f"{conv.title.replace(' ', '_')}.md", "content": md_content}
