"""Manus API v2 backend for BR-JARVIS.

Manus is task-oriented rather than OpenAI-compatible: a completion creates or
continues a task, then polls ``task.listMessages`` until the agent stops.
Credentials are read from the environment and are never included in logs.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Generator
from typing import Any

import requests

from .base import BaseBackend

logger = logging.getLogger("JARVIS.Manus")


class ManusAPIError(RuntimeError):
    """Raised when the Manus API rejects a request or a task fails."""


class ManusBackend(BaseBackend):
    """Adapter for the official Manus API v2 task lifecycle."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model or os.getenv("MANUS_AGENT_PROFILE", "manus-1.6-lite")
        self.api_key = (api_key or os.getenv("MANUS_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("MANUS_API_BASE_URL", "https://api.manus.ai")).rstrip("/")
        self.timeout = float(os.getenv("MANUS_HTTP_TIMEOUT", "30"))
        self.poll_timeout = float(os.getenv("MANUS_TIMEOUT_SECONDS", "180"))
        self.poll_interval = max(0.25, float(os.getenv("MANUS_POLL_INTERVAL_SECONDS", "1.0")))
        self.task_id = os.getenv("MANUS_TASK_ID", "").strip() or None
        self._seen_event_ids: set[str] = set()
        self._session = requests.Session()
        self._session.headers.update({"x-manus-api-key": self.api_key, "Content-Type": "application/json"})

    @property
    def name(self) -> str:
        return "Manus"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _check_response(self, response: requests.Response, operation: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise ManusAPIError(f"Manus returned invalid JSON during {operation} (HTTP {response.status_code})") from exc

        if not response.ok or data.get("ok") is False:
            error = data.get("error") if isinstance(data, dict) else None
            message = error.get("message", "request rejected") if isinstance(error, dict) else "request rejected"
            raise ManusAPIError(f"Manus {operation} failed (HTTP {response.status_code}): {message}")
        return data

    @staticmethod
    def _message_text(messages: list[dict[str, Any]], system: str, tools: list | None) -> str:
        parts: list[str] = []
        if system.strip():
            parts.append(f"System instructions:\n{system.strip()}")
        for message in messages[-12:]:
            role = str(message.get("role", "user")).capitalize()
            content = message.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content
                )
            if content:
                parts.append(f"{role}:\n{content}")
        if tools:
            parts.append(
                "The calling application may have local tools. Do not claim to have executed a local tool; return the "
                "best direct answer unless the user explicitly asks for a Manus-side action."
            )
        prompt = "\n\n".join(parts).strip()
        # Manus documents an approximately 5,000-token input limit. Keep a generous
        # character bound so normal conversations stay below that limit.
        return prompt[-18000:]

    def _create_task(self, prompt: str) -> str:
        payload = {
            "message": {"content": [{"type": "text", "text": prompt}]},
            "agent_profile": self.model,
            "interactive_mode": False,
            "hide_in_task_list": True,
            "title": "BR-JARVIS request",
        }
        response = self._session.post(f"{self.base_url}/v2/task.create", json=payload, timeout=self.timeout)
        data = self._check_response(response, "task.create")
        task_id = str(data.get("task_id", "")).strip()
        if not task_id:
            raise ManusAPIError("Manus task.create returned no task_id")
        self.task_id = task_id
        self._seen_event_ids.clear()
        return task_id

    def _send_message(self, prompt: str, task_id: str) -> None:
        payload = {
            "task_id": task_id,
            "message": {"content": [{"type": "text", "text": prompt}]},
            "agent_profile": self.model,
        }
        response = self._session.post(f"{self.base_url}/v2/task.sendMessage", json=payload, timeout=self.timeout)
        self._check_response(response, "task.sendMessage")

    def _poll_result(self, task_id: str) -> str:
        deadline = time.monotonic() + self.poll_timeout
        not_found_deadline = time.monotonic() + min(15.0, self.poll_timeout)
        newest_answer = ""
        while time.monotonic() < deadline:
            try:
                response = self._session.get(
                    f"{self.base_url}/v2/task.listMessages",
                    params={"task_id": task_id, "order": "desc", "limit": 50},
                    timeout=self.timeout,
                )
                data = self._check_response(response, "task.listMessages")
            except ManusAPIError as exc:
                # Newly created tasks can take a few seconds to become visible to
                # task.listMessages. Retry only during that initial consistency
                # window; permanent 404s still fail with a useful error.
                if "HTTP 404" in str(exc) and time.monotonic() < not_found_deadline:
                    time.sleep(self.poll_interval)
                    continue
                raise
            events = data.get("messages", [])
            if not isinstance(events, list):
                raise ManusAPIError("Manus task.listMessages returned an invalid messages field")

            status = "running"
            for event in events:
                if not isinstance(event, dict):
                    continue
                event_id = str(event.get("id", ""))
                is_new = not event_id or event_id not in self._seen_event_ids
                if event_id:
                    self._seen_event_ids.add(event_id)
                status_update = event.get("status_update") or {}
                if isinstance(status_update, dict) and status_update.get("agent_status") and status == "running":
                    # Results are requested in descending order, so keep the
                    # newest status event instead of allowing an older event to
                    # overwrite it.
                    status = str(status_update["agent_status"])
                if event.get("type") == "assistant_message":
                    assistant = event.get("assistant_message") or {}
                    if isinstance(assistant, dict) and assistant.get("content") and (is_new or not newest_answer):
                        newest_answer = str(assistant["content"])
                if is_new and event.get("type") == "error_message":
                    error = event.get("error_message") or {}
                    detail = error.get("content", "unknown task error") if isinstance(error, dict) else str(error)
                    raise ManusAPIError(f"Manus task failed: {detail}")

            if status == "stopped":
                if newest_answer:
                    return newest_answer
                # The assistant event may arrive immediately after the status event;
                # one short follow-up fetch avoids returning an empty answer.
                time.sleep(min(self.poll_interval, 0.5))
            elif status == "error":
                raise ManusAPIError("Manus task ended with an error")
            elif status == "waiting":
                raise ManusAPIError(
                    "Manus task is waiting for confirmation or user input; configure an explicit confirmation flow "
                    "before using this request."
                )
            else:
                time.sleep(self.poll_interval)

        raise ManusAPIError(f"Manus task timed out after {self.poll_timeout:g} seconds")

    def complete(self, messages: list[dict], system: str = "", tools: list | None = None) -> str:
        if not self.api_key:
            return "ERROR: MANUS_API_KEY is not configured."
        prompt = self._message_text(messages, system, tools)
        if not prompt:
            prompt = "Please respond to the user's request."
        try:
            if self.task_id:
                self._send_message(prompt, self.task_id)
            else:
                self._create_task(prompt)
            return self._poll_result(self.task_id or "")
        except requests.Timeout as exc:
            logger.warning("Manus request timed out")
            return f"ERROR: Manus request timed out: {exc.__class__.__name__}"
        except requests.RequestException as exc:
            logger.warning("Manus network request failed: %s", exc.__class__.__name__)
            return "ERROR: Manus service is unreachable."
        except ManusAPIError as exc:
            logger.warning("Manus completion failed: %s", exc)
            return f"ERROR: {exc}"

    def stream(self, messages: list[dict], system: str = "") -> Generator[str, None, None]:
        result = self.complete(messages, system=system)
        if not result:
            return
        for index in range(0, len(result), 120):
            yield result[index : index + 120]

    def ping(self, timeout: float = 3.0) -> bool:
        if not self.api_key:
            return False
        try:
            response = self._session.get(
                f"{self.base_url}/v2/task.listMessages",
                params={"task_id": "agent-default-main_task", "limit": 1},
                timeout=min(timeout, self.timeout),
            )
            return response.status_code in {200, 403, 404}
        except requests.RequestException:
            return False


__all__ = ["ManusAPIError", "ManusBackend"]

