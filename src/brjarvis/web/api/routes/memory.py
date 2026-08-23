# api/routes/memory.py — Memory, Contacts, Notes & Document Ingestion Endpoints
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from brjarvis.core.paths import paths

logger = logging.getLogger("JARVIS.API.Memory")
router = APIRouter(tags=["Memory"])

_BASE_DIR = paths.PROJECT_ROOT


class SaveMemoryRequest(BaseModel):
    name: str
    type: str
    description: str
    content: str
    scope: str = "user"


class RememberRequest(BaseModel):
    text: str


class AddContactRequest(BaseModel):
    name: str
    phone_number: str = ""
    email: str = ""
    aliases: List[str] = []


@router.get("/memory")
async def list_memories(scope: str = "all"):
    """List persistent memories."""
    from brjarvis.memory.persistent_store import load_entries

    scopes = ["user", "project"] if scope == "all" else [scope]
    entries = []
    for s in scopes:
        for e in load_entries(s):
            entries.append(
                {
                    "name": e.name,
                    "description": e.description,
                    "type": e.type,
                    "content": e.content,
                    "scope": e.scope,
                    "created": e.created,
                }
            )
    return {"memories": entries}


@router.post("/memory")
async def save_memory_entry(req: SaveMemoryRequest):
    """Save/update a persistent memory entry."""
    from brjarvis.memory.persistent_store import MemoryEntry, save_memory

    entry = MemoryEntry(
        name=req.name,
        description=req.description,
        type=req.type,
        content=req.content,
        created=time.strftime("%Y-%m-%d"),
    )
    save_memory(entry, scope=req.scope)
    return {"message": f"Memory '{req.name}' saved successfully."}


@router.delete("/memory/{name}")
async def delete_memory_entry(name: str, scope: str = "user"):
    """Delete a persistent memory entry."""
    from brjarvis.memory.persistent_store import delete_memory

    delete_memory(name, scope=scope)
    return {"message": f"Memory '{name}' deleted successfully."}


@router.get("/contacts")
async def get_contacts_endpoint(query: str = Query("", description="Search filter query")):
    """Get contacts list from UnifiedContactStore with optional search filter."""
    from brjarvis.memory.contact_manager import get_contact_store

    store = get_contact_store()
    results = store.search_contacts(query) if query else store.get_all_contacts()
    return {"total": len(results), "contacts": results}


@router.post("/contacts")
async def add_contact_endpoint(req: AddContactRequest):
    """Add a new contact directly to the UnifiedContactStore."""
    from brjarvis.memory.contact_manager import get_contact_store

    store = get_contact_store()
    try:
        result = store.add_contact(
            name=req.name,
            phone_number=req.phone_number,
            email=req.email,
            aliases=req.aliases,
        )
        return {"status": "success", "message": f"Contact '{req.name}' added.", "contact": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add contact: {e}")


@router.post("/import/contacts")
async def import_contacts_endpoint(
    file: UploadFile = File(None),
    content: str = Form(None),
    file_path: str = Form(None),
):
    """Import contacts from uploaded .vcf/.csv file or file path."""
    from brjarvis.memory.contact_manager import get_contact_store

    store = get_contact_store()

    if file:
        file_bytes = await file.read()
        text_str = file_bytes.decode("utf-8", errors="replace")
        filename = file.filename or "contacts.txt"
        if filename.lower().endswith(".vcf") or "BEGIN:VCARD" in text_str.upper():
            res = store.import_vcf(text_str)
        else:
            res = store.import_csv(text_str)
        return {"status": "success", "file_name": filename, "result": res}

    if file_path:
        p = Path(file_path).expanduser().resolve()
        try:
            p.relative_to(paths.WORKSPACE_ROOT.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="file_path must be inside the configured workspace root.") from exc
        if not p.exists() or not p.is_file():
            raise HTTPException(status_code=404, detail="Contact import file was not found.")
        if p.suffix.lower() == ".vcf":
            res = store.import_vcf(p)
        else:
            res = store.import_csv(p)
        return {"status": "success", "file_name": p.name, "result": res}

    if content:
        if "BEGIN:VCARD" in content.upper():
            res = store.import_vcf(content)
        else:
            res = store.import_csv(content)
        return {"status": "success", "result": res}

    raise HTTPException(status_code=400, detail="Provide a file upload, file_path, or text content to import.")


@router.post("/import/file")
async def import_file_endpoint(
    file: UploadFile = File(None),
    file_path: str = Form(None),
):
    """Import document or knowledge file (.pdf, .docx, .txt, .md, .csv, .vcf) into memory & vector store."""
    from brjarvis.actions.file_importer import import_file_to_knowledge

    if file:
        temp_dir = paths.TEMP_ROOT / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(file.filename or "upload.bin").name
        save_path = temp_dir / filename
        file_bytes = await file.read()
        save_path.write_bytes(file_bytes)
        res = import_file_to_knowledge(save_path)
        return res

    if file_path:
        res = import_file_to_knowledge(file_path)
        return res

    raise HTTPException(status_code=400, detail="Provide a file upload or file_path to import.")


@router.post("/remember")
async def remember_note(req: RememberRequest):
    """Save a voice or text note into captures/ and update 3D galaxy live."""
    try:
        text = req.text.strip()
        if text.lower().startswith("remember that "):
            text = text[14:].strip()
        elif text.lower().startswith("remember "):
            text = text[9:].strip()

        words = text.split()
        title_slug = "_".join(words[:4]).lower() if words else "note"
        title_slug = re.sub(r"[^a-z0-9_]", "", title_slug) or "capture"

        captures_dir = paths.CAPTURE_ROOT
        captures_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{title_slug}_{int(time.time())}.md"
        filepath = captures_dir / filename

        title = " ".join(words[:4]).title() if words else "Voice Capture"
        content = f"# {title}\n\n**Captured**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{text}\n"
        filepath.write_text(content, encoding="utf-8")

        from brjarvis.actions.rag_library import scan_markdown_notes

        graph_data = scan_markdown_notes(str(_BASE_DIR))
        new_node_index = len(graph_data["nodes"]) - 1

        confirmation = f"Recorded to your brain, sir: '{title}'."
        return {
            "status": "success",
            "title": title,
            "filename": filename,
            "node_index": new_node_index,
            "graph": graph_data,
            "confirmation": confirmation,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/galaxy/data")
async def get_galaxy_data():
    """Return 3D Knowledge Galaxy nodes and links from scanned notes."""
    try:
        from brjarvis.actions.rag_library import scan_markdown_notes

        return scan_markdown_notes(str(_BASE_DIR))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
