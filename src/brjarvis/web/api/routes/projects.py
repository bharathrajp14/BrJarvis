# api/routes/projects.py — Project Workspace Endpoints for BR JARVIS MK40.2 / MK41
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from brjarvis.core.paths import paths
from brjarvis.memory.workspace_store import get_workspace_store

logger = logging.getLogger("JARVIS.API.Projects")
router = APIRouter(tags=["Projects"])
_MAX_PROJECT_FILE_BYTES = 25 * 1024 * 1024
_MAX_PREVIEW_BYTES = 1 * 1024 * 1024
_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".yaml", ".yml", ".log", ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".xml"}


def _public_file_dict(record):
    data = record.to_dict()
    raw_path = data.pop("file_path", None)
    data["path"] = Path(raw_path).name if raw_path else data.get("filename", "")
    return data


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
        "files": [_public_file_dict(f) for f in files],
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
    return {"total": len(files), "files": [_public_file_dict(f) for f in files]}


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
    if not filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="A valid filename is required")
    target_path = target_dir / filename

    content = await file.read(_MAX_PROJECT_FILE_BYTES + 1)
    if len(content) > _MAX_PROJECT_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"Project files are limited to {_MAX_PROJECT_FILE_BYTES // (1024 * 1024)} MiB")
    temp_path = target_dir / f".{filename}.{uuid.uuid4().hex}.upload"
    try:
        temp_path.write_bytes(content)
        temp_path.replace(target_path)
    finally:
        temp_path.unlink(missing_ok=True)

    rec = store.add_project_file(
        project_id=project_id,
        filename=filename,
        file_path=str(target_path),
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="READY",
    )
    return {"status": "success", "file": _public_file_dict(rec)}


@router.get("/projects/{project_id}/files/{file_id}/preview")
async def preview_project_file(project_id: str, file_id: str):
    """Return safe metadata and a bounded preview for a project file."""
    store = get_workspace_store()
    record = store.get_project_file(project_id, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    expected_root = (paths.ARTIFACT_ROOT / "projects" / project_id).resolve()
    file_path = Path(record.file_path).expanduser().resolve()
    try:
        file_path.relative_to(expected_root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Project file is outside the project workspace") from exc
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Project file is not available")
    suffix = file_path.suffix.lower()
    is_text = record.mime_type.startswith("text/") or suffix in _TEXT_EXTENSIONS
    payload = {"file_id": record.file_id, "project_id": record.project_id, "filename": record.filename, "mime_type": record.mime_type, "size": file_path.stat().st_size, "is_text": is_text}
    if is_text:
        raw = file_path.read_bytes()[:_MAX_PREVIEW_BYTES]
        payload["content"] = raw.decode("utf-8", errors="replace")
        payload["truncated"] = file_path.stat().st_size > _MAX_PREVIEW_BYTES
    return payload


@router.delete("/projects/{project_id}/files/{file_id}")
async def delete_project_file(project_id: str, file_id: str):
    """Remove a file from the project workspace."""
    store = get_workspace_store()
    success = store.delete_project_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "success", "message": "File removed."}
