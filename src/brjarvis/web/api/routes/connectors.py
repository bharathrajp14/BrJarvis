# api/routes/connectors.py — Modernized Dynamic Connector Hub Endpoints
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("JARVIS.API.Connectors")
router = APIRouter(tags=["Connectors"])

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_SETTINGS_FILE = _CONFIG_DIR / "connector_settings.json"
_LEGACY_API_FILE = _CONFIG_DIR / "api_keys.json"
_CONNECTORS_CACHE: dict | None = None
_CONNECTORS_CACHE_TS = 0.0
_CACHE_TTL_SECONDS = 3.0


def _migrate_legacy_connector_secrets() -> None:
    """Move legacy connector API keys to the OS vault and scrub the old JSON file."""
    if not _LEGACY_API_FILE.exists():
        return
    try:
        legacy = json.loads(_LEGACY_API_FILE.read_text(encoding="utf-8"))
        if not isinstance(legacy, dict):
            return
        secret_entries = {
            str(key): str(value).strip()
            for key, value in legacy.items()
            if str(key).lower().endswith(("_api_key", "_token")) and isinstance(value, str) and value.strip()
        }
        if not secret_entries:
            return
        from brjarvis.security.credentials import get_credential_vault

        vault = get_credential_vault()
        for key, value in secret_entries.items():
            connector_id = key.rsplit("_", 1)[0].lower()
            vault.store_credential(
                _credential_reference(connector_id),
                value,
                metadata={"connector_id": connector_id, "kind": "api_key", "migrated_from": "api_keys.json"},
            )
        sanitized = {key: value for key, value in legacy.items() if key not in secret_entries}
        temp_file = _LEGACY_API_FILE.with_suffix(".json.migrated")
        temp_file.write_text(json.dumps(sanitized, indent=2, sort_keys=True), encoding="utf-8")
        temp_file.replace(_LEGACY_API_FILE)
        logger.warning("Migrated %d legacy connector secrets to secure storage", len(secret_entries))
    except Exception as exc:
        # Never delete legacy values if secure migration did not complete.
        logger.error("Legacy connector secret migration could not complete securely: %s", exc)


def _read_settings() -> dict:
    """Read connector settings only; secret values belong in CredentialVault."""
    _migrate_legacy_connector_secrets()
    try:
        if _SETTINGS_FILE.exists():
            payload = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("Unable to read connector settings metadata: %s", exc)
    return {}


def _credential_reference(connector_id: str) -> str:
    return f"connector:{connector_id}:api_key"


class ConnectorCallRequest(BaseModel):
    connector: Optional[str] = None
    connector_id: Optional[str] = None
    tool: str
    params: Dict[str, Any] = {}

    def get_connector(self) -> str:
        return (self.connector or self.connector_id or "").strip()


class ConnectorConfigRequest(BaseModel):
    connector: Optional[str] = None
    connector_id: Optional[str] = None
    api_key: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

    def get_connector(self) -> str:
        return (self.connector or self.connector_id or "").strip()


class ConnectorTestRequest(BaseModel):
    connector: Optional[str] = None
    connector_id: Optional[str] = None

    def get_connector(self) -> str:
        return (self.connector or self.connector_id or "").strip()


def _categorize_connector(cid: str) -> str:
    cid = cid.lower()
    if cid in ("telegram", "slack", "gmail", "whatsapp"):
        return "Communication"
    elif cid in ("web_search", "wikipedia", "rss_news", "weather"):
        return "Search & Knowledge"
    elif cid in ("calendar", "notion", "filesystem", "github"):
        return "Productivity & Dev"
    return "System & MCP"


@router.get("/connectors")
async def get_connectors_list():
    """List all dynamically discovered App Connectors with live status, tool inventories & auth hints."""
    _migrate_legacy_connector_secrets()
    global _CONNECTORS_CACHE, _CONNECTORS_CACHE_TS
    now = time.time()
    if _CONNECTORS_CACHE is not None and (now - _CONNECTORS_CACHE_TS) < _CACHE_TTL_SECONDS:
        return _CONNECTORS_CACHE

    from connectors.hub import get_hub

    hub = get_hub()
    raw_connectors = hub.list_connectors()

    formatted_connectors = []
    for c in raw_connectors:
        cid = c.get("id", "")
        name = c.get("name", cid.capitalize())
        desc = c.get("description", "")
        icon = c.get("icon", "🔌")
        is_conf = bool(c.get("configured", False))
        req_auth = bool(c.get("requires_auth", False))
        tools = c.get("tools", [])
        tool_names = [t.get("name", "") for t in tools if isinstance(t, dict)]

        status = "CONNECTED" if is_conf else "NOT_CONFIGURED"

        formatted_connectors.append(
            {
                "id": cid,
                "name": name,
                "desc": desc,
                "icon": icon,
                "status": status,
                "configured": is_conf,
                "requires_auth": req_auth,
                "auth_hint": c.get("auth_hint", ""),
                "category": _categorize_connector(cid),
                "tools": tool_names,
                "tool_details": tools,
                "tool_count": len(tools),
            }
        )

    payload = {
        "status": "ok",
        "count": len(formatted_connectors),
        "active_count": sum(1 for c in formatted_connectors if c["configured"]),
        "connectors": formatted_connectors,
    }
    _CONNECTORS_CACHE = payload
    _CONNECTORS_CACHE_TS = now
    return payload


@router.get("/connector/status")
async def connector_status():
    """Return status of all registered connectors in the Connector Hub."""
    return await get_connectors_list()


@router.get("/connector/list")
async def connector_list():
    """Return all connectors and their available tools dictionary."""
    try:
        from connectors.hub import get_hub

        hub = get_hub()
        result = {}
        for c in hub.list_connectors():
            result[c["name"]] = {
                "id": c.get("id", ""),
                "icon": c.get("icon", "🔌"),
                "configured": c.get("configured", False),
                "tools": c.get("tools", []),
                "description": c.get("description", ""),
            }
        return {"status": "ok", "connectors": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector/call")
async def connector_call(req: ConnectorCallRequest):
    """Call a specific connector tool by connector ID/name and tool name."""
    try:
        conn_id = req.get_connector()
        if not conn_id:
            raise HTTPException(status_code=400, detail="Missing 'connector' or 'connector_id' in request.")
        from connectors.hub import get_hub

        hub = get_hub()
        result = await asyncio.to_thread(hub.call, conn_id, req.tool, req.params)
        return {"status": "ok", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing connector tool %s/%s: %s", req.get_connector(), req.tool, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector/test")
async def connector_test(req: ConnectorTestRequest):
    """Test live connectivity and latency for a specific connector."""
    conn_id = req.get_connector()
    if not conn_id:
        raise HTTPException(status_code=400, detail="Missing 'connector' or 'connector_id' in request.")
    from connectors.hub import get_hub

    hub = get_hub()
    conn = hub.get_connector(conn_id)
    if not conn:
        for c in hub._connectors.values():
            if c.display_name.lower() == conn_id.lower():
                conn = c
                break

    if not conn:
        raise HTTPException(status_code=404, detail=f"Connector '{conn_id}' not found.")

    t0 = time.perf_counter()
    try:
        is_healthy = await asyncio.to_thread(conn.health_check)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "status": "ok" if is_healthy else "degraded",
            "connector": conn.connector_id,
            "display_name": conn.display_name,
            "healthy": is_healthy,
            "latency_ms": latency_ms,
            "message": f"Connection verified in {latency_ms}ms"
            if is_healthy
            else "Health check reported degraded state",
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "status": "error",
            "connector": conn.connector_id,
            "display_name": conn.display_name,
            "healthy": False,
            "latency_ms": latency_ms,
            "error": str(exc),
            "message": f"Connection test failed: {exc}",
        }


@router.post("/connector/config")
async def save_connector_config(req: ConnectorConfigRequest):
    """Save API key or configuration settings for a specific connector."""
    global _CONNECTORS_CACHE
    _CONNECTORS_CACHE = None
    try:
        conn_id = req.get_connector()
        if not conn_id:
            raise HTTPException(status_code=400, detail="Missing 'connector' or 'connector_id' in request.")
        conn_name = conn_id.lower().strip()
        settings = _read_settings()

        if req.api_key:
            val = req.api_key.strip()
            if not val:
                raise HTTPException(status_code=422, detail="api_key cannot be empty.")
            from brjarvis.security.credentials import get_credential_vault

            credential_ref = _credential_reference(conn_name)
            get_credential_vault().store_credential(
                credential_ref,
                val,
                metadata={"connector_id": conn_name, "kind": "api_key"},
            )
            # Keep provider adapters compatible at runtime without serializing the secret.
            os.environ[f"{conn_name.upper()}_API_KEY"] = val
            if "github" in conn_name:
                os.environ["GITHUB_TOKEN"] = val
            elif "notion" in conn_name:
                os.environ["NOTION_TOKEN"] = val
                os.environ["NOTION_API_KEY"] = val
            elif "slack" in conn_name:
                os.environ["SLACK_BOT_TOKEN"] = val
            elif "telegram" in conn_name:
                os.environ["TELEGRAM_BOT_TOKEN"] = val
            elif "tavily" in conn_name or "search" in conn_name:
                os.environ["TAVILY_API_KEY"] = val
            elif "youtube" in conn_name:
                os.environ["YOUTUBE_API_KEY"] = val

        if req.settings and isinstance(req.settings, dict):
            settings[f"{conn_name}_settings"] = req.settings
            for k, v in req.settings.items():
                if isinstance(v, str) and v.strip():
                    os.environ[k.upper()] = v.strip()

        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _SETTINGS_FILE.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")
        logger.info("[ConnectorConfig] Saved metadata for '%s'", conn_name)
        return {
            "status": "ok",
            "connector": conn_name,
            "credential_ref": _credential_reference(conn_name) if req.api_key else None,
            "message": f"Saved configuration for '{conn_name}'",
        }
    except Exception as e:
        logger.error("[ConnectorConfig] Error saving config: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
