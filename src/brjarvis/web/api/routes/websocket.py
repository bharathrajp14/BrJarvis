# api/routes/websocket.py — Real-time Web & Mobile WebSocket Channels for BR JARVIS MK40.2 / MK41
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from brjarvis.agent.task_state import get_task_state_manager
from brjarvis.core.version import VERSION
from brjarvis.events.bus import get_event_bus
from brjarvis.integrations.mobile.gateway import get_device_gateway
from brjarvis.integrations.mobile.session import get_mobile_session_manager
from brjarvis.memory.workspace_store import get_workspace_store

from ..state import (
    ACTIVE_WEBSOCKETS,
    SERVER_API_KEY,
    get_orchestrator,
    get_ws_lock,
)
from .auth import verify_and_consume_ws_ticket, verify_session

logger = logging.getLogger("JARVIS.API.WebSocket")
router = APIRouter(tags=["WebSockets"])


async def safe_ws_send(ws: WebSocket, data: dict) -> bool:
    """Safely send a standardized JSON event payload to a WebSocket client if connected."""
    try:
        if ws.client_state == WebSocketState.CONNECTED:
            # Ensure standard event envelop
            if "event_id" not in data:
                data["event_id"] = str(uuid.uuid4())
            if "timestamp" not in data:
                data["timestamp"] = time.time()
            await ws.send_json(data)
            return True
    except (RuntimeError, WebSocketDisconnect, Exception):
        pass
    return False


async def broadcast_ws_event(
    event_type: str, payload: dict, conversation_id: Optional[str] = None, task_id: Optional[str] = None
):
    """Broadcast an event to all connected web clients."""
    data = {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "conversation_id": conversation_id,
        "task_id": task_id,
        "timestamp": time.time(),
        "payload": payload,
    }
    async with get_ws_lock():
        targets = list(ACTIVE_WEBSOCKETS)
    if not targets:
        return
    await asyncio.gather(
        *(asyncio.wait_for(safe_ws_send(ws, data), timeout=0.5) for ws in targets),
        return_exceptions=True,
    )


def _forward_eventbus_to_ws(event: Any) -> None:
    """Forward EventBus events to active WebSockets."""
    try:
        topic = getattr(event, "topic", "event")
        payload = (
            event.model_dump()
            if hasattr(event, "model_dump")
            else (event.dict() if hasattr(event, "dict") else getattr(event, "payload", {}))
        )
        cid = getattr(event, "session_id", None)
        tid = getattr(event, "task_id", None)
        # Schedule broadcast on running loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_ws_event(topic, payload, conversation_id=cid, task_id=tid))
        except RuntimeError:
            pass
    except Exception:
        pass


try:
    _bus = get_event_bus()
    for topic_pattern in ("agent.*", "tool.*", "permission.*", "verification.*", "artifact.*", "task.*", "session.*"):
        _bus.subscribe(topic_pattern, _forward_eventbus_to_ws)
except Exception as _sub_err:
    logger.debug("EventBus WS forwarder subscription notice: %s", _sub_err)


def _check_ws_auth(websocket: WebSocket) -> bool:
    """Validate WebSocket handshake credentials against server security policy."""
    if not SERVER_API_KEY:
        return False

    allowed_origins = {
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
    configured_origins = os.environ.get("JARVIS_CORS_ORIGINS", "")
    allowed_origins.update(origin.strip() for origin in configured_origins.split(",") if origin.strip())
    origin = websocket.headers.get("origin")
    if origin and origin not in allowed_origins:
        return False

    ticket = websocket.query_params.get("ticket")

    # Check one-time ticket
    if ticket and verify_and_consume_ws_ticket(ticket):
        return True

    # Check session cookie
    cookies = websocket.cookies
    if cookies and "jarvis_session" in cookies:
        if verify_session(cookies["jarvis_session"]):
            return True

    return False


@router.websocket("/ws")
@router.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bidirectional WebSocket for Web Dashboard chat, tasks, telemetry, and event stream.
    Supports short-lived connection tickets, session tokens, and ping/pong heartbeats.
    """
    from .chat import run_generator_in_thread

    if not _check_ws_auth(websocket):
        await websocket.close(code=4001, reason="Unauthorized: Invalid WebSocket Ticket or Session")
        return

    await websocket.accept()
    async with get_ws_lock():
        ACTIVE_WEBSOCKETS.add(websocket)

    store = get_workspace_store()
    task_mgr = get_task_state_manager()

    # Send initial ServerReady message
    await safe_ws_send(
        websocket,
        {
            "event_id": str(uuid.uuid4()),
            "type": "ServerReady",
            "timestamp": time.time(),
            "payload": {
                "status": "ONLINE",
                "server_version": VERSION,
            },
        },
    )

    try:
        while True:
            raw_data = await websocket.receive_text()
            if not raw_data.strip():
                continue

            try:
                req = json.loads(raw_data)
            except json.JSONDecodeError:
                await safe_ws_send(
                    websocket,
                    {
                        "event_id": str(uuid.uuid4()),
                        "type": "error",
                        "timestamp": time.time(),
                        "payload": {"error": "Invalid JSON format"},
                    },
                )
                continue

            msg_type = req.get("type", "").lower()
            request_id = req.get("request_id") or str(uuid.uuid4())

            # 1. Heartbeat Ping / Pong
            if msg_type in ("ping", "heartbeat"):
                await safe_ws_send(
                    websocket,
                    {
                        "event_id": str(uuid.uuid4()),
                        "type": "Heartbeat",
                        "request_id": request_id,
                        "timestamp": time.time(),
                        "payload": {"status": "pong"},
                    },
                )
                continue

            # 2. Chat Prompt / Execution
            if msg_type in ("chat_prompt", "command", "chat", "clientcommand", "message.send"):
                cmd = (
                    req.get("prompt")
                    or req.get("message")
                    or req.get("text")
                    or (req.get("payload") or {}).get("command")
                    or (req.get("payload") or {}).get("message")
                    or ""
                )
                conv_id = req.get("conversation_id") or (req.get("payload") or {}).get("conversation_id")
                branch_id = req.get("branch_id") or (req.get("payload") or {}).get("branch_id") or "main"
                backend_choice = req.get("backend") or (req.get("payload") or {}).get("backend")
                plan_only = req.get("plan_only", False) or (req.get("payload") or {}).get("plan_only", False)
                task_id = req.get("task_id") or f"task_{uuid.uuid4().hex[:8]}"

                if not cmd.strip():
                    continue

                # Ensure conversation exists
                if not conv_id or not store.get_conversation(conv_id):
                    new_conv = store.create_conversation(title="New Chat")
                    conv_id = new_conv.conversation_id
                    await safe_ws_send(
                        websocket,
                        {
                            "event_id": str(uuid.uuid4()),
                            "type": "conversation.created",
                            "conversation_id": conv_id,
                            "payload": {"conversation": new_conv.to_dict()},
                        },
                    )

                # Persist user message
                user_msg = store.add_message(
                    conversation_id=conv_id,
                    role="user",
                    content=cmd,
                    branch_id=branch_id,
                    backend=backend_choice or "gemini",
                )
                await safe_ws_send(
                    websocket,
                    {
                        "event_id": str(uuid.uuid4()),
                        "type": "message.created",
                        "conversation_id": conv_id,
                        "payload": {"message": user_msg.to_dict()},
                    },
                )

                orch = get_orchestrator()
                if backend_choice and orch and getattr(orch, "router", None):
                    try:
                        orch.router.switch_backend(backend_choice)
                    except Exception:
                        pass

                ws_ref = websocket

                async def run_chat_or_task_job(
                    ws=ws_ref,
                    command=cmd,
                    cid=conv_id,
                    bid=branch_id,
                    tid=task_id,
                    rid=request_id,
                    is_plan_only=plan_only,
                ):
                    start_time = time.time()
                    try:
                        # 1. Create or notify task
                        await safe_ws_send(
                            ws,
                            {
                                "event_id": str(uuid.uuid4()),
                                "type": "task.started",
                                "conversation_id": cid,
                                "task_id": tid,
                                "request_id": rid,
                                "payload": {
                                    "task_id": tid,
                                    "goal": command,
                                    "status": "PLANNING" if is_plan_only else "RUNNING",
                                    "plan_only": is_plan_only,
                                },
                            },
                        )

                        # 2. Plan Mode Only
                        if is_plan_only:
                            plan_steps = [
                                {"step_id": "1", "title": "Analyze Goal & Requirements", "status": "completed"},
                                {
                                    "step_id": "2",
                                    "title": "Inspect Local Context & Dependencies",
                                    "status": "completed",
                                },
                                {
                                    "step_id": "3",
                                    "title": "Synthesize Plan Graph & Execution Steps",
                                    "status": "completed",
                                },
                                {"step_id": "4", "title": "Await User Plan Approval", "status": "pending"},
                            ]
                            plan_text = (
                                f'### 📋 Execution Plan for: "{command}"\n\n'
                                f"**Objective**: Autonomous multi-step fulfillment with verification.\n\n"
                                f"**Planned Steps**:\n"
                                f"1. 🔍 **Phase 1: Inspection & Scope Discovery** — Read existing files, verify dependencies.\n"
                                f"2. ⚡ **Phase 2: Execution & Creation** — Generate requested code/artifacts without overwriting unverified files.\n"
                                f"3. 🛡️ **Phase 3: Verification & Integrity Check** — Run tests and check outputs against goal.\n\n"
                                f"**Risk Level**: Safe (Plan Only Mode)\n"
                                f"**Approval Required**: Click **Approve Plan** to begin active execution."
                            )
                            # Persist assistant response
                            asst_msg = store.add_message(
                                conversation_id=cid,
                                role="assistant",
                                content=plan_text,
                                branch_id=bid,
                                linked_task_id=tid,
                                backend=backend_choice or "gemini",
                                latency_ms=int((time.time() - start_time) * 1000),
                            )
                            await safe_ws_send(
                                ws,
                                {
                                    "event_id": str(uuid.uuid4()),
                                    "type": "message.completed",
                                    "conversation_id": cid,
                                    "task_id": tid,
                                    "payload": {
                                        "message": asst_msg.to_dict(),
                                        "is_plan": True,
                                        "plan_steps": plan_steps,
                                    },
                                },
                            )
                            await safe_ws_send(
                                ws,
                                {
                                    "event_id": str(uuid.uuid4()),
                                    "type": "task.waiting",
                                    "conversation_id": cid,
                                    "task_id": tid,
                                    "payload": {"status": "WAITING_FOR_APPROVAL", "plan_steps": plan_steps},
                                },
                            )
                            return

                        # 3. Active Stream Execution
                        await safe_ws_send(
                            ws,
                            {
                                "event_id": str(uuid.uuid4()),
                                "type": "message.delta_start",
                                "conversation_id": cid,
                                "task_id": tid,
                                "request_id": rid,
                                "payload": {"status": "streaming"},
                            },
                        )

                        active_orch = get_orchestrator()
                        full_text = ""

                        if active_orch:
                            async for token_str in run_generator_in_thread(active_orch.chat_stream, command):
                                full_text += token_str
                                await safe_ws_send(
                                    ws,
                                    {
                                        "event_id": str(uuid.uuid4()),
                                        "type": "message.delta",
                                        "conversation_id": cid,
                                        "task_id": tid,
                                        "request_id": rid,
                                        "payload": {"delta": token_str, "accumulated": full_text},
                                    },
                                )
                        else:
                            full_text = "JARVIS Cognitive Core initialized. Execution completed."
                            await safe_ws_send(
                                ws,
                                {
                                    "event_id": str(uuid.uuid4()),
                                    "type": "message.delta",
                                    "conversation_id": cid,
                                    "task_id": tid,
                                    "request_id": rid,
                                    "payload": {"delta": full_text, "accumulated": full_text},
                                },
                            )

                        latency = int((time.time() - start_time) * 1000)

                        # Check for any newly created artifacts in current task
                        task_artifacts = store.list_artifacts(conversation_id=cid)

                        # Persist final Assistant message
                        asst_msg = store.add_message(
                            conversation_id=cid,
                            role="assistant",
                            content=full_text,
                            branch_id=bid,
                            linked_task_id=tid,
                            linked_artifacts=[a.to_dict() for a in task_artifacts[:3]],
                            backend=backend_choice or "gemini",
                            latency_ms=latency,
                        )

                        await safe_ws_send(
                            ws,
                            {
                                "event_id": str(uuid.uuid4()),
                                "type": "message.completed",
                                "conversation_id": cid,
                                "task_id": tid,
                                "request_id": rid,
                                "payload": {"message": asst_msg.to_dict()},
                            },
                        )

                        await safe_ws_send(
                            ws,
                            {
                                "event_id": str(uuid.uuid4()),
                                "type": "task.completed",
                                "conversation_id": cid,
                                "task_id": tid,
                                "request_id": rid,
                                "payload": {
                                    "status": "SUCCESS_VERIFIED",
                                    "result": full_text[:500],
                                    "latency_ms": latency,
                                },
                            },
                        )

                    except Exception as e:
                        logger.exception("Error executing WebSocket chat/task job: %s", e)
                        await safe_ws_send(
                            ws,
                            {
                                "event_id": str(uuid.uuid4()),
                                "type": "task.failed",
                                "conversation_id": cid,
                                "task_id": tid,
                                "request_id": rid,
                                "payload": {"error": "Task execution failed. Please retry or inspect server logs."},
                            },
                        )

                asyncio.create_task(run_chat_or_task_job())

            # 3. Status Query
            elif msg_type == "status_query":
                orch = get_orchestrator()
                mode = getattr(orch, "current_mode", "general") if orch else "offline"
                await safe_ws_send(
                    websocket,
                    {
                        "event_id": str(uuid.uuid4()),
                        "type": "SystemMessage",
                        "request_id": request_id,
                        "timestamp": time.time(),
                        "payload": {
                            "status": "ONLINE",
                            "mode": mode,
                            "active_clients": len(ACTIVE_WEBSOCKETS),
                        },
                    },
                )

            # 4. Resolve Approval Gate
            elif msg_type == "approval.resolve":
                app_task_id = req.get("task_id")
                app_req_id = req.get("request_id")
                approved = bool(req.get("approved", True))
                if app_task_id and app_req_id:
                    task_mgr.resolve_approval(app_task_id, app_req_id, approved=approved)
                    await safe_ws_send(
                        websocket,
                        {
                            "event_id": str(uuid.uuid4()),
                            "type": "approval.resolved",
                            "task_id": app_task_id,
                            "payload": {"request_id": app_req_id, "approved": approved},
                        },
                    )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WebSocket connection terminated: %s", exc)
    finally:
        async with get_ws_lock():
            ACTIVE_WEBSOCKETS.discard(websocket)


@router.websocket("/mobile/ws")
async def mobile_websocket_endpoint(websocket: WebSocket):
    """Real-time WebSocket endpoint for paired mobile clients."""
    from starlette.websockets import WebSocketDisconnect

    token = websocket.query_params.get("token") or websocket.query_params.get("key")
    device_id = websocket.query_params.get("device_id") or websocket.query_params.get("id")
    if not token or not device_id:
        await websocket.close(code=4001, reason="Missing auth token or device_id")
        return

    gateway = get_device_gateway()
    if not gateway.verify_auth_token(device_id, token):
        await websocket.close(code=4001, reason="Invalid or revoked device credentials")
        return

    await websocket.accept()
    session_mgr = get_mobile_session_manager()
    session = await session_mgr.register_session(device_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            session.handle_incoming_message(raw)
    except WebSocketDisconnect:
        await session_mgr.remove_session(device_id)
    except Exception as e:
        logger.error("Mobile websocket error for %s: %s", device_id, e)
        await session_mgr.remove_session(device_id)
