# api/routes/projects.py — Project Workspace Endpoints for BR JARVIS MK40.2 / MK41
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from brjarvis.core.paths import paths
from brjarvis.memory.workspace_store import get_workspace_store

logger = logging.getLogger("JARVIS.API.Projects")
router = APIRouter(tags=["Projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    instructions: Optional[str] = ""
    settings: Optional[Dict[str, Any]] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    pinned: Optional[bool] = None


@router.get("/projects")
async def list_projects():
    """List all workspace projects."""
    store = get_workspace_store()
    projects = store.list_projects()
    return {"total": len(projects), "projects": [p.to_dict() for p in projects]}


@router.post("/projects")
async def create_project(req: CreateProjectRequest):
    """Create a new workspace project."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    store = get_workspace_store()
    proj = store.create_project(
        name=req.name.strip(),
        description=req.description or "",
        instructions=req.instructions or "",
        settings=req.settings or {},
    )
    return {"status": "success", "project": proj.to_dict()}


@router.get("/projects/{project_id}")
async def get_project_details(project_id: str):
    """Get project details including files, conversations, tasks, and artifacts."""
    store = get_workspace_store()
    proj = store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    files = store.list_project_files(project_id)
    convs = store.list_conversations(project_id=project_id)
    artifacts = store.list_artifacts(project_id=project_id)

    return {
        "project": proj.to_dict(),
        "files": [f.to_dict() for f in files],
        "conversations": [c.to_dict() for c in convs],
        "artifacts": [a.to_dict() for a in artifacts],
    }


@router.patch("/projects/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest):
    """Update project metadata, instructions, and settings."""
    store = get_workspace_store()
    updated = store.update_project(
        project_id=project_id,
        name=req.name,
        description=req.description,
        instructions=req.instructions,
        settings=req.settings,
        pinned=req.pinned,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "project": updated.to_dict()}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project workspace."""
    store = get_workspace_store()
    success = store.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": f"Project {project_id} deleted."}


@router.get("/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """List all files attached to a project."""
    store = get_workspace_store()
    files = store.list_project_files(project_id)
    return {"total": len(files), "files": [f.to_dict() for f in files]}


@router.post("/projects/{project_id}/files")
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
):
    """Upload a document/file and link it to the project workspace."""
    store = get_workspace_store()
    proj = store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    target_dir = paths.ARTIFACT_ROOT / "projects" / project_id
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename or "upload.bin").name
    target_path = target_dir / filename

    content = await file.read()
    target_path.write_bytes(content)

    rec = store.add_project_file(
        project_id=project_id,
        filename=filename,
        file_path=str(target_path),
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="READY",
    )
    return {"status": "success", "file": rec.to_dict()}


@router.delete("/projects/{project_id}/files/{file_id}")
async def delete_project_file(project_id: str, file_id: str):
    """Remove a file from the project workspace."""
    store = get_workspace_store()
    success = store.delete_project_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "success", "message": "File removed."}
