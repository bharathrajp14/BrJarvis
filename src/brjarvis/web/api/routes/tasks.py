# api/routes/tasks.py — Autonomous Task Management & Approval Routes
from __future__ import annotations

import logging
import threading
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brjarvis.agent.task_queue import TaskPriority, get_queue
from brjarvis.agent.task_state import get_task_state_manager

logger = logging.getLogger("JARVIS.API.Tasks")
router = APIRouter(tags=["Tasks"])


class CreateTaskRequest(BaseModel):
    goal: str
    active_devices: Optional[List[str]] = None
    mode: str = "smart"
    privacy: str = "balanced"


class ResolveApprovalRequest(BaseModel):
    request_id: str
    approved: bool


class RunRequest(BaseModel):
    goals: List[str]


@router.get("/tasks")
async def get_tasks():
    """Retrieve queue tasks status."""
    try:
        q = get_queue()
        statuses = q.get_all_statuses()
        return {"active": q.active_count(), "pending": q.pending_count(), "tasks": statuses[-10:]}
    except Exception:
        logger.exception("Failed to list queue tasks")
        raise HTTPException(status_code=500, detail="Unable to list tasks")


@router.post("/run")
async def run_parallel(req: RunRequest):
    """Submit goals to the task queue."""
    if not req.goals:
        raise HTTPException(status_code=400, detail="No goals specified")
    try:
        q = get_queue()
        task_ids = q.submit_many(req.goals, priority=TaskPriority.NORMAL)
        return {"status": "started", "task_ids": task_ids}
    except Exception:
        logger.exception("Failed to submit parallel tasks")
        raise HTTPException(status_code=500, detail="Unable to start tasks")


@router.get("/agent/tasks")
async def list_agent_tasks(status: Optional[str] = None, limit: int = 50):
    """List active and historical tasks from the persistent TaskStateManager."""
    mgr = get_task_state_manager()
    tasks = mgr.list_tasks(status=status, limit=limit)
    return {"total": len(tasks), "tasks": [t.to_dict() for t in tasks]}


@router.get("/agent/tasks/{task_id}")
async def get_agent_task(task_id: str):
    """Retrieve detailed task state, steps, and checkpoints by task_id."""
    mgr = get_task_state_manager()
    task = mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/agent/tasks")
async def create_agent_task(req: CreateTaskRequest):
    """Create and trigger an autonomous task via AgentExecutor."""
    from brjarvis.agent.executor import AgentExecutor

    mgr = get_task_state_manager()
    mode = req.mode if req.mode in {"fast", "smart", "deep"} else "smart"
    privacy = req.privacy if req.privacy in {"balanced", "local_only"} else "balanced"
    task = mgr.create_task(
        req.goal,
        active_devices=req.active_devices,
        goal_spec={"execution_mode": mode, "privacy": privacy},
    )

    def _run_job():
        try:
            executor = AgentExecutor()
            executor.execute(req.goal, task_id=task.task_id)
        except Exception as e:
            logger.error("Background task execution error: %s", e)

    threading.Thread(target=_run_job, daemon=True).start()
    return {"status": "started", "task_id": task.task_id, "goal": req.goal}


@router.post("/agent/tasks/{task_id}/approve")
async def approve_agent_task(task_id: str, req: ResolveApprovalRequest):
    """Approve or reject a pending high-risk action approval gate."""
    mgr = get_task_state_manager()
    updated = mgr.resolve_approval(task_id, req.request_id, approved=req.approved)
    if not updated:
        raise HTTPException(status_code=400, detail="Unable to resolve approval request")
    return {"status": "resolved", "task": updated.to_dict()}
