# gateway/model_gateway.py — OpenAI-Compatible Proxy Brain Gateway Client
"""
Standard Model Gateway adapter for BR JARVIS.
Communicates with the local OpenAI-compatible Proxy Brain (default: http://localhost:8045/v1).
Provides response normalization, model discovery, error handling, and credential safety.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Generator, Optional

import requests

from .models_registry import ModelRegistry, get_model_registry

logger = logging.getLogger("JARVIS.ModelGateway")

_DEFAULT_FALLBACK_CHAIN = [
    "antigravity/gemini-3.7-flash-high",
    "antigravity/claude-sonnet-4-6",
    "antigravity/claude-opus-4-6-thinking",
    "groq/qwen/qwen3.8-27b",
    "antigravity/gemini-3.1-flash-lite",
]

_MODEL_COOLDOWNS: dict[str, float] = {}


# ── Response Schema & Exceptions ─────────────────────────────────────────────


@dataclass
class ModelResponse:
    """Normalized response envelope returned by all model completions."""

    text: str
    tool_calls: list[dict] = field(default_factory=list)
    finish_reason: str = "stop"
    model: str = ""
    usage: dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    latency_ms: float = 0.0
    provider: str = "proxy_brain"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    raw: Optional[Any] = None

    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


class ModelGatewayError(Exception):
    """Base exception for all gateway errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, model: Optional[str] = None):
        sanitized = _sanitize_error_msg(message)
        super().__init__(sanitized)
        self.status_code = status_code
        self.model = model


class GatewayUnavailableError(ModelGatewayError):
    """Raised when the Proxy Brain gateway cannot be reached."""

    pass


class ModelNotFoundError(ModelGatewayError):
    """Raised when the requested model is not exposed or supported by the gateway."""

    pass


class MalformedResponseError(ModelGatewayError):
    """Raised when the model generates invalid or unparseable structured data."""

    pass


class GatewayTimeoutError(ModelGatewayError):
    """Raised when a gateway completion times out."""

    pass


class GatewayAuthenticationError(ModelGatewayError):
    """Raised when authentication with the gateway fails."""

    pass


def _sanitize_error_msg(msg: str) -> str:
    """Strip any accidental credential patterns from error messages."""
    if not msg:
        return ""
    # Redact Bearer tokens, raw hex/alphanumeric keys
    msg = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", msg, flags=re.IGNORECASE)
    msg = re.sub(r"key=[\'\"]?[A-Za-z0-9_\-\.]{8,}[\'\"]?", "key=[REDACTED]", msg, flags=re.IGNORECASE)
    msg = re.sub(
        r"api[-_]?key[\'\"]?\s*:\s*[\'\"]?[A-Za-z0-9_\-\.]{8,}[\'\"]?", "api_key: [REDACTED]", msg, flags=re.IGNORECASE
    )
    return msg


# ── Gateway Configuration Helper ─────────────────────────────────────────────


def _load_gateway_config() -> dict[str, Any]:
    base_url = os.environ.get("BRJARVIS_PROXY_BASE_URL", "").strip() or os.environ.get("OPENAI_BASE_URL", "").strip()
    api_key = os.environ.get("BRJARVIS_PROXY_API_KEY", "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()

    # Load from api_keys.json if not present in env
    if not api_key or not base_url:
        try:
            from brjarvis.core.paths import paths

            key_file = paths.CONFIG_ROOT / "api_keys.json"
            if key_file.exists():
                data = json.loads(key_file.read_text(encoding="utf-8"))
                base_url = base_url or data.get("proxy_base_url") or data.get("openai_base_url")
                api_key = api_key or data.get("proxy_api_key") or data.get("openai_api_key")
        except Exception:
            pass

    base_url = (base_url or "http://127.0.0.1:20128/v1").strip()
    api_key = (api_key or "sk-5ec70bf9fa324084b7a7326babf52c45").strip()

    timeout_s = float(os.environ.get("BRJARVIS_REQUEST_TIMEOUT", "60.0"))
    connect_timeout_s = float(os.environ.get("BRJARVIS_CONNECT_TIMEOUT", "10.0"))
    privacy_mode = os.environ.get("BRJARVIS_PRIVACY_MODE", "proxy_only").strip().lower()
    allow_cloud = os.environ.get("BRJARVIS_ALLOW_CLOUD_FALLBACK", "false").strip().lower() in ("true", "1", "yes")

    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "timeout_seconds": timeout_s,
        "connect_timeout_seconds": connect_timeout_s,
        "privacy_mode": privacy_mode,
        "allow_direct_cloud_fallback": allow_cloud,
    }


# ── ModelGateway Client Implementation ───────────────────────────────────────


class ModelGateway:
    """Central OpenAI-compatible client adapter for the Proxy Brain gateway."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        registry: Optional[ModelRegistry] = None,
    ):
        cfg = _load_gateway_config()
        self.base_url = (base_url or cfg["base_url"]).rstrip("/")
        self.api_key = api_key or cfg["api_key"]
        self.timeout = timeout_seconds or cfg["timeout_seconds"]
        self.connect_timeout = cfg["connect_timeout_seconds"]
        self.privacy_mode = cfg["privacy_mode"]
        self.allow_cloud_fallback = cfg["allow_direct_cloud_fallback"]
        self.registry = registry or get_model_registry()

        self._discovered_models: Optional[set[str]] = None
        self._discovery_ts: float = 0.0
        self._discovery_ttl: float = 300.0  # 5 minutes

        self._init_client()

    def _init_client(self):
        """Initialize the underlying client with safety checks."""
        # Privacy Enforcement: verify that the base_url does not point to direct cloud endpoints in proxy_only mode
        is_direct_cloud = any(
            cloud in self.base_url.lower() for cloud in ("openai.com", "googleapis.com", "anthropic.com")
        )
        if is_direct_cloud and not self.allow_cloud_fallback and self.privacy_mode in ("proxy_only", "local_only"):
            raise ValueError(
                f"[Gateway Privacy Violation] Direct cloud endpoint '{self.base_url}' is blocked under active privacy mode '{self.privacy_mode}'."
            )

        self._openai_client = None
        try:
            from openai import OpenAI

            self._openai_client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=1,
            )
            logger.info("OpenAI SDK client initialized pointing to %s", self.base_url)
        except ImportError:
            logger.info("OpenAI SDK not available; using resilient HTTP client fallback for %s", self.base_url)

    def discover_models(self, force_refresh: bool = False) -> set[str]:
        """Query GET /v1/models from the Proxy Brain to discover active model IDs."""
        now = time.time()
        if (
            not force_refresh
            and self._discovered_models is not None
            and (now - self._discovery_ts) < self._discovery_ttl
        ):
            return set(self._discovered_models)

        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(url, headers=headers, timeout=self.connect_timeout)
            if resp.status_code == 200:
                data = resp.json()
                models = set()
                for item in data.get("data", []):
                    m_id = item.get("id")
                    if m_id:
                        models.add(m_id)
                self._discovered_models = models
                self._discovery_ts = now
                logger.info("Discovered %d models from Proxy Brain gateway: %s", len(models), sorted(models))
                return set(models)
            elif resp.status_code in (401, 403):
                raise GatewayAuthenticationError(
                    f"Gateway authentication failed: HTTP {resp.status_code}", status_code=resp.status_code
                )
            else:
                logger.debug("Model discovery returned status %d; using static registry catalog", resp.status_code)
        except requests.RequestException as exc:
            logger.debug("Proxy Brain discovery notice: %s; using static registry catalog", exc)

        # Fallback to catalog from registry
        return set(self.registry.list_ids())

    def ping(self, timeout: float = 3.0) -> bool:
        """Fast healthcheck ping to Proxy Brain gateway."""
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            return r.status_code in (200, 404)  # 200 means healthy, 404 still indicates reachable server
        except Exception:
            return False

    def _get_candidate_models(self, primary_model: str) -> list[str]:
        """Return prioritized list of healthy candidate models with fallback hierarchy."""
        now = time.time()
        # Clean expired cooldowns
        expired = [m for m, exp in _MODEL_COOLDOWNS.items() if exp <= now]
        for m in expired:
            _MODEL_COOLDOWNS.pop(m, None)

        ordered = [primary_model]
        for m in _DEFAULT_FALLBACK_CHAIN:
            if m not in ordered:
                ordered.append(m)

        # Prioritize non-cooling-down models
        healthy = [m for m in ordered if _MODEL_COOLDOWNS.get(m, 0) <= now]
        cooling = [m for m in ordered if _MODEL_COOLDOWNS.get(m, 0) > now]
        return healthy + cooling

    def complete(
        self,
        messages: list[dict],
        model: str = "gemini-3.6-flash-high",
        system: str = "",
        tools: Optional[list[dict]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        response_format: Optional[dict] = None,
        request_id: Optional[str] = None,
    ) -> ModelResponse:
        """Synchronous chat completion with silent automatic failover across verified models."""
        start_time = time.monotonic()
        req_id = request_id or str(uuid.uuid4())

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        candidate_models = self._get_candidate_models(model)
        last_exception: Optional[Exception] = None

        # 1. Try candidates via OpenAI SDK with silent failover
        if self._openai_client is not None:
            for cand_model in candidate_models[:4]:
                try:
                    kwargs: dict[str, Any] = {
                        "model": cand_model,
                        "messages": full_messages,
                        "temperature": temperature,
                    }
                    if max_tokens:
                        kwargs["max_tokens"] = max_tokens
                    if tools:
                        kwargs["tools"] = tools
                    if response_format:
                        kwargs["response_format"] = response_format

                    resp = self._openai_client.chat.completions.create(timeout=10.0, **kwargs)
                    elapsed_ms = (time.monotonic() - start_time) * 1000.0

                    choice = resp.choices[0] if resp.choices else None
                    text = (choice.message.content or "") if choice and getattr(choice, "message", None) else ""
                    tool_calls = []
                    if choice and getattr(choice.message, "tool_calls", None):
                        for tc in choice.message.tool_calls:
                            tool_calls.append(
                                {
                                    "id": getattr(tc, "id", str(uuid.uuid4())),
                                    "name": tc.function.name,
                                    "arguments": json.loads(tc.function.arguments)
                                    if isinstance(tc.function.arguments, str)
                                    else tc.function.arguments,
                                }
                            )

                    # If response is non-empty or has tool calls, succeed immediately
                    if text.strip() or tool_calls:
                        if cand_model != model:
                            logger.info(
                                "[ModelGateway] Silently auto-switched model from '%s' to '%s'", model, cand_model
                            )

                        usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                        if getattr(resp, "usage", None):
                            usage_dict = {
                                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                                "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
                            }

                        return ModelResponse(
                            text=text,
                            tool_calls=tool_calls,
                            finish_reason=(choice.finish_reason if choice else "stop") or "stop",
                            model=cand_model,
                            usage=usage_dict,
                            latency_ms=round(elapsed_ms, 2),
                            provider="proxy_brain",
                            request_id=req_id,
                            raw=resp,
                        )

                    # Empty text returned: mark cooldown and try next model
                    _MODEL_COOLDOWNS[cand_model] = time.time() + 60.0
                    logger.debug("[ModelGateway] Model '%s' returned empty response; auto-switching", cand_model)

                except Exception as exc:
                    _MODEL_COOLDOWNS[cand_model] = time.time() + 60.0
                    logger.debug("[ModelGateway] Model '%s' notice: %s; auto-switching", cand_model, exc)
                    last_exception = exc

        # 2. Resilient Direct HTTP Fallback on best candidate
        target_model = candidate_models[0] if candidate_models else model
        try:
            return self._complete_http(
                full_messages=full_messages,
                model=target_model,
                tools=tools,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
                req_id=req_id,
                start_time=start_time,
            )
        except Exception as exc:
            if last_exception is not None:
                self._handle_client_exception(last_exception, model)
            self._handle_client_exception(exc, target_model)

    def _complete_http(
        self,
        full_messages: list[dict],
        model: str,
        tools: Optional[list[dict]],
        max_tokens: Optional[int],
        temperature: float,
        response_format: Optional[dict],
        req_id: str,
        start_time: float,
    ) -> ModelResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "model": model,
            "messages": full_messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if response_format:
            payload["response_format"] = response_format

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            elapsed_ms = (time.monotonic() - start_time) * 1000.0

            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                if not choices:
                    raise MalformedResponseError(f"Gateway returned no choices for model '{model}'", model=model)
                choice = choices[0]
                msg = choice.get("message", {})
                text = msg.get("content") or ""

                tool_calls = []
                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {})
                    args_val = fn.get("arguments", {})
                    if isinstance(args_val, str):
                        try:
                            args_val = json.loads(args_val)
                        except Exception:
                            pass
                    tool_calls.append(
                        {"id": tc.get("id", str(uuid.uuid4())), "name": fn.get("name", ""), "arguments": args_val}
                    )

                usage_data = data.get("usage", {})
                return ModelResponse(
                    text=text,
                    tool_calls=tool_calls,
                    finish_reason=choice.get("finish_reason", "stop"),
                    model=model,
                    usage={
                        "prompt_tokens": usage_data.get("prompt_tokens", 0),
                        "completion_tokens": usage_data.get("completion_tokens", 0),
                        "total_tokens": usage_data.get("total_tokens", 0),
                    },
                    latency_ms=round(elapsed_ms, 2),
                    provider="proxy_brain",
                    request_id=req_id,
                    raw=data,
                )
            elif r.status_code == 404:
                raise ModelNotFoundError(
                    f"Model '{model}' not found on Proxy Brain gateway (HTTP 404)", status_code=404, model=model
                )
            elif r.status_code in (401, 403):
                raise GatewayAuthenticationError(
                    f"Gateway auth error (HTTP {r.status_code})", status_code=r.status_code, model=model
                )
            elif r.status_code == 504:
                raise GatewayTimeoutError(
                    f"Gateway timeout (HTTP 504) for model '{model}'", status_code=504, model=model
                )
            else:
                raise ModelGatewayError(
                    f"Gateway HTTP error {r.status_code}: {r.text}", status_code=r.status_code, model=model
                )

        except requests.Timeout as exc:
            raise GatewayTimeoutError(
                f"Request to Proxy Brain timed out after {self.timeout}s: {exc}", model=model
            ) from exc
        except requests.ConnectionError as exc:
            raise GatewayUnavailableError(
                f"Failed to connect to Proxy Brain at {self.base_url}: {exc}", model=model
            ) from exc
        except Exception as exc:
            if isinstance(exc, ModelGatewayError):
                raise
            raise ModelGatewayError(f"Unexpected gateway error: {exc}", model=model) from exc

    def stream(
        self,
        messages: list[dict],
        model: str = "gemini-3.6-flash-high",
        system: str = "",
        tools: Optional[list[dict]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Streaming chat completion with silent automatic failover across verified models."""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        candidate_models = self._get_candidate_models(model)

        # 1. Try OpenAI SDK streaming with candidate failover
        if self._openai_client is not None:
            for cand_model in candidate_models[:3]:
                try:
                    kwargs: dict[str, Any] = {
                        "model": cand_model,
                        "messages": full_messages,
                        "temperature": temperature,
                        "stream": True,
                    }
                    if max_tokens:
                        kwargs["max_tokens"] = max_tokens
                    if tools:
                        kwargs["tools"] = tools

                    stream_resp = self._openai_client.chat.completions.create(timeout=10.0, **kwargs)
                    yielded_any = False
                    for chunk in stream_resp:
                        if chunk.choices and chunk.choices[0].delta:
                            content = chunk.choices[0].delta.content
                            if content:
                                yielded_any = True
                                yield content
                    if yielded_any:
                        return
                except Exception as exc:
                    _MODEL_COOLDOWNS[cand_model] = time.time() + 60.0
                    logger.debug("[ModelGateway] SDK stream error for '%s': %s", cand_model, exc)

        # 2. HTTP Server-Sent Events Streaming
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
            yield f"[Stream Error: {_sanitize_error_msg(str(exc))}]"

    def _handle_client_exception(self, exc: Exception, model: str):
        err_str = str(exc).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise GatewayTimeoutError(f"Gateway request timed out: {exc}", model=model) from exc
        elif "connect" in err_str or "connection" in err_str or "refused" in err_str:
            raise GatewayUnavailableError(
                f"Could not connect to Proxy Brain at {self.base_url}: {exc}", model=model
            ) from exc
        elif (
            "404" in err_str
            or "not found" in err_str
            or "unknown model" in err_str
            or "quota for model" in err_str
            or "nonexistent" in err_str
        ):
            raise ModelNotFoundError(
                f"Model '{model}' not found or unavailable on Proxy Brain: {exc}", status_code=404, model=model
            ) from exc
        elif "401" in err_str or "403" in err_str or "unauthorized" in err_str:
            raise GatewayAuthenticationError(
                f"Gateway authentication error: {exc}", status_code=401, model=model
            ) from exc
        else:
            raise ModelGatewayError(f"Gateway execution error: {exc}", model=model) from exc


_global_gateway: Optional[ModelGateway] = None


def get_model_gateway() -> ModelGateway:
    """Return the global ModelGateway singleton."""
    global _global_gateway
    if _global_gateway is None:
        _global_gateway = ModelGateway()
    return _global_gateway
