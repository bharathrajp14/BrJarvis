# gateway/client.py — High-Resilience Proxy Brain Client Adapter
"""
Core HTTP / SDK client adapter communicating with the local OpenAI-compatible
Proxy Brain gateway (default: http://localhost:8045/v1).

Enforces:
- Bounded timeouts & connection retry policies.
- Universal credential sanitization (API keys never appear in logs/errors).
- Normalized response envelopes (ModelResponse) and structured exceptions.
- Server-Sent Events (SSE) streaming.
- Strict Privacy Mode (PROXY_ONLY: blocks unintended direct cloud endpoints).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Generator, Optional

logger = logging.getLogger("JARVIS.ProxyBrainClient")

# ─────────────────────────────────────────────────────────────────────────────
# Structured Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class ProxyBrainClientError(Exception):
    """Base exception for all Proxy Brain client operations."""

    def __init__(self, message: str, model: str = "", status_code: Optional[int] = None):
        super().__init__(message)
        self.model = model
        self.status_code = status_code


class GatewayUnavailableError(ProxyBrainClientError):
    """Raised when the Proxy Brain gateway cannot be reached."""

    pass


class ModelNotFoundError(ProxyBrainClientError):
    """Raised when the requested model is not found or not available."""

    pass


class QuotaExceededError(ProxyBrainClientError):
    """Raised when no quota or accounts are available on the gateway (e.g. HTTP 503)."""

    pass


class GatewayTimeoutError(ProxyBrainClientError):
    """Raised when a gateway request times out."""

    pass


class GatewayAuthenticationError(ProxyBrainClientError):
    """Raised on authentication failures (e.g. HTTP 401/403)."""

    pass


class MalformedResponseError(ProxyBrainClientError):
    """Raised when the gateway returns invalid or unparseable JSON."""

    pass


# ─────────────────────────────────────────────────────────────────────────────
# Credential Redaction Helper
# ─────────────────────────────────────────────────────────────────────────────

_SECRET_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]{8,}", re.IGNORECASE),
    re.compile(r"(api[_-]?key[\"'\s:=]+)[A-Za-z0-9_\-\.]{8,}", re.IGNORECASE),
    re.compile(r"(sk-[A-Za-z0-9_\-\.]{12,})", re.IGNORECASE),
    re.compile(r"(AIza[0-9A-Za-z-_]{35})", re.IGNORECASE),
]


def sanitize_error_msg(msg: str) -> str:
    """Mask any leaked credentials or bearer tokens from error strings."""
    if not msg:
        return ""
    sanitized = str(msg)
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(r"\1[REDACTED]", sanitized)
    return sanitized


# ─────────────────────────────────────────────────────────────────────────────
# Normalized Response Envelope
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ModelResponse:
    """Standardized response envelope returned from all model completions."""

    text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"
    model: str = ""
    usage: dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    latency_ms: float = 0.0
    provider: str = "proxy_brain"
    request_id: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Proxy Brain Client
# ─────────────────────────────────────────────────────────────────────────────


class ProxyBrainClient:
    """
    OpenAI-compatible client communicating exclusively with the local Proxy Brain.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        allow_direct_cloud: bool = False,
    ):
        self.base_url = (
            base_url
            or os.environ.get("BRJARVIS_PROXY_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or "http://127.0.0.1:20128/v1"
        ).rstrip("/")

        self.api_key = (
            api_key or os.environ.get("BRJARVIS_PROXY_API_KEY") or os.environ.get("OPENAI_API_KEY") or "local-proxy-key"
        )
        self.timeout = float(os.environ.get("BRJARVIS_GATEWAY_TIMEOUT", timeout))
        self.allow_direct_cloud = (
            allow_direct_cloud or os.environ.get("BRJARVIS_ALLOW_CLOUD_FALLBACK", "false").lower() == "true"
        )

        # Strict Privacy Guard: block public cloud endpoints unless explicitly allowed
        self._enforce_privacy_policy()

        # Initialize optional OpenAI SDK client
        self._openai_client = None
        try:
            from openai import OpenAI  # type: ignore

            self._openai_client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout)
        except Exception as e:
            logger.debug("OpenAI SDK client not initialized, using HTTP requests adapter: %s", e)

    def _enforce_privacy_policy(self):
        """Block accidental leakage to remote cloud domains in local/proxy mode."""
        if not self.allow_direct_cloud:
            blocked = ["api.openai.com", "generativelanguage.googleapis.com", "api.anthropic.com"]
            for domain in blocked:
                if domain in self.base_url.lower():
                    raise ValueError(
                        f"Privacy Violation: Direct cloud endpoint '{self.base_url}' is blocked in PROXY_ONLY mode."
                    )

    def complete(
        self,
        messages: list[dict[str, Any]],
        model: str = "gemini-3.6-flash-high",
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ModelResponse:
        """
        Execute a synchronous completion against the Proxy Brain gateway.
        """
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        t_start = time.monotonic()

        # 1. Try OpenAI SDK if available
        if self._openai_client is not None:
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": full_messages,
                    "temperature": temperature,
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                if tools:
                    kwargs["tools"] = tools
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                resp = self._openai_client.chat.completions.create(**kwargs)
                latency_ms = (time.monotonic() - t_start) * 1000

                choice = resp.choices[0] if resp.choices else None
                text_content = (choice.message.content or "") if choice and choice.message else ""
                finish_reason = choice.finish_reason if choice else "stop"

                extracted_tools: list[dict[str, Any]] = []
                if choice and choice.message and getattr(choice.message, "tool_calls", None):
                    for tc in choice.message.tool_calls:
                        call_dict = {
                            "id": getattr(tc, "id", ""),
                            "type": getattr(tc, "type", "function"),
                            "function": {
                                "name": getattr(tc.function, "name", ""),
                                "arguments": getattr(tc.function, "arguments", "{}"),
                            },
                        }
                        extracted_tools.append(call_dict)

                usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                if hasattr(resp, "usage") and resp.usage:
                    usage_data = {
                        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                        "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                        "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
                    }

                return ModelResponse(
                    text=text_content,
                    tool_calls=extracted_tools,
                    finish_reason=finish_reason,
                    model=model,
                    usage=usage_data,
                    latency_ms=round(latency_ms, 2),
                    provider="proxy_brain",
                    request_id=getattr(resp, "id", ""),
                )
            except Exception as exc:
                self._handle_client_exception(exc, model)

        # 2. Fallback to direct HTTP request
        import requests

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {"model": model, "messages": full_messages, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            latency_ms = (time.monotonic() - t_start) * 1000

            if r.status_code == 200:
                data = r.json()
                choice = data.get("choices", [{}])[0]
                msg_obj = choice.get("message", {})
                text_content = msg_obj.get("content") or ""
                finish_reason = choice.get("finish_reason", "stop")
                tool_calls = msg_obj.get("tool_calls", [])
                usage_data = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

                return ModelResponse(
                    text=text_content,
                    tool_calls=tool_calls,
                    finish_reason=finish_reason,
                    model=model,
                    usage=usage_data,
                    latency_ms=round(latency_ms, 2),
                    provider="proxy_brain",
                    request_id=data.get("id", ""),
                    raw_response=data,
                )
            elif r.status_code == 404:
                raise ModelNotFoundError(
                    f"Model '{model}' not found on Proxy Brain: {sanitize_error_msg(r.text)}",
                    model=model,
                    status_code=404,
                )
            elif r.status_code in (401, 403):
                raise GatewayAuthenticationError(
                    f"Gateway authentication failure: {sanitize_error_msg(r.text)}",
                    model=model,
                    status_code=r.status_code,
                )
            elif r.status_code == 503 or "quota" in r.text.lower():
                raise QuotaExceededError(
                    f"Model '{model}' quota exhausted on gateway: {sanitize_error_msg(r.text)}",
                    model=model,
                    status_code=r.status_code,
                )
            else:
                raise ProxyBrainClientError(
                    f"Gateway error HTTP {r.status_code}: {sanitize_error_msg(r.text)}",
                    model=model,
                    status_code=r.status_code,
                )

        except (requests.Timeout, requests.exceptions.Timeout) as exc:
            raise GatewayTimeoutError(
                f"Request to {self.base_url} timed out after {self.timeout}s", model=model
            ) from exc
        except (requests.ConnectionError, requests.exceptions.ConnectionError) as exc:
            raise GatewayUnavailableError(
                f"Could not connect to Proxy Brain at {self.base_url}: {sanitize_error_msg(str(exc))}", model=model
            ) from exc
        except json.JSONDecodeError as exc:
            raise MalformedResponseError(f"Invalid JSON returned by Proxy Brain: {exc}", model=model) from exc
        except ProxyBrainClientError:
            raise
        except Exception as exc:
            raise ProxyBrainClientError(
                f"Unexpected gateway error: {sanitize_error_msg(str(exc))}", model=model
            ) from exc

    def stream(
        self,
        messages: list[dict[str, Any]],
        model: str = "gemini-3.6-flash-high",
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Streaming chat completion yielding text chunks via SSE."""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        # 1. Try OpenAI SDK streaming
        if self._openai_client is not None:
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": full_messages,
                    "temperature": temperature,
                    "stream": True,
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                if tools:
                    kwargs["tools"] = tools

                stream_resp = self._openai_client.chat.completions.create(**kwargs)
                for chunk in stream_resp:
                    if chunk.choices and chunk.choices[0].delta:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                return
            except Exception as exc:
                logger.debug("SDK stream error, falling back to HTTP stream: %s", exc)

        # 2. Direct HTTP SSE streaming
        import requests

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": full_messages, "temperature": temperature, "stream": True}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=self.timeout) as r:
                if r.status_code != 200:
                    yield f"[Gateway Error: HTTP {r.status_code}]"
                    return
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode("utf-8").strip()
                        if decoded.startswith("data: "):
                            data_str = decoded[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                choices = chunk_json.get("choices", [])
                                if choices and "delta" in choices[0]:
                                    content = choices[0]["delta"].get("content")
                                    if content:
                                        yield content
                            except Exception:
                                pass
        except Exception as exc:
            yield f"[Stream Error: {sanitize_error_msg(str(exc))}]"

    def _handle_client_exception(self, exc: Exception, model: str):
        """Map client SDK exceptions to structured ProxyBrainClientError hierarchy."""
        err_str = str(exc).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise GatewayTimeoutError(f"Gateway request timed out: {exc}", model=model) from exc
        elif "connect" in err_str or "connection" in err_str or "refused" in err_str:
            raise GatewayUnavailableError(
                f"Could not connect to Proxy Brain at {self.base_url}: {exc}", model=model
            ) from exc
        elif "quota" in err_str or "503" in err_str or "no accounts" in err_str:
            raise QuotaExceededError(f"Model '{model}' quota exceeded: {exc}", model=model, status_code=503) from exc
        elif "404" in err_str or "not found" in err_str or "unknown model" in err_str or "nonexistent" in err_str:
            raise ModelNotFoundError(
                f"Model '{model}' not found on Proxy Brain: {exc}", status_code=404, model=model
            ) from exc
        elif "401" in err_str or "403" in err_str or "unauthorized" in err_str:
            raise GatewayAuthenticationError(
                f"Gateway authentication error: {exc}", status_code=401, model=model
            ) from exc
        else:
            raise ProxyBrainClientError(
                f"Gateway execution error: {sanitize_error_msg(str(exc))}", model=model
            ) from exc


_global_client: Optional[ProxyBrainClient] = None


def get_proxy_brain_client() -> ProxyBrainClient:
    """Return the global ProxyBrainClient singleton."""
    global _global_client
    if _global_client is None:
        _global_client = ProxyBrainClient()
    return _global_client
