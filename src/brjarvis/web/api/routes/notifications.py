# api/routes/notifications.py — System & Task Notifications Endpoints
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brjarvis.memory.workspace_store import get_workspace_store

logger = logging.getLogger("JARVIS.API.Notifications")
router = APIRouter(tags=["Notifications"])


class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    category: Optional[str] = "ALL"
    severity: Optional[str] = "info"
    action_link: Optional[str] = None


@router.get("/notifications")
async def list_notifications(
    category: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
):
    """List system, task, career, and security notifications."""
    store = get_workspace_store()
    notifs = store.list_notifications(category=category, unread_only=unread_only, limit=limit)
    unread_count = len([n for n in notifs if not n.is_read])
    return {
        "total": len(notifs),
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifs],
    }


@router.post("/notifications")
async def create_notification(req: CreateNotificationRequest):
    """Create a new notification entry."""
    store = get_workspace_store()
    notif = store.add_notification(
        title=req.title,
        message=req.message,
        category=req.category or "ALL",
        severity=req.severity or "info",
        action_link=req.action_link,
    )
    return {"status": "success", "notification": notif.to_dict()}


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark single notification as read."""
    store = get_workspace_store()
    success = store.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "notification_id": notification_id}


@router.post("/notifications/read-all")
async def mark_all_notifications_read():
    """Mark all unread notifications as read."""
    store = get_workspace_store()
    count = store.mark_all_notifications_read()
    return {"status": "success", "marked_read": count}
