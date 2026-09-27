"""OpenAI and OpenAI-compatible provider adapter."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from ..contracts import ModelRequest, ModelResponse
from ..errors import ProviderAuthenticationError, ProviderRateLimitError, ProviderRequestError, ProviderResponseError
from .base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI SDK clients and compatible proxy endpoints."""

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
        provider: str = "openai",
        models: frozenset[str] | None = None,
        capabilities: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            default_model=model,
            models=models,
            capabilities=capabilities or frozenset({"chat", "code", "reasoning", "vision"}),
        )
        self._client = client
        self._api_key = api_key or ""
        self._base_url = base_url
        if self._client is None:
            try:
                from openai import OpenAI

                kwargs: dict[str, Any] = {"api_key": self._api_key or "local-development"}
                if base_url:
                    kwargs["base_url"] = base_url
                self._client = OpenAI(**kwargs)
            except (ImportError, Exception):
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _messages(self, request: ModelRequest) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(request.messages)
        return messages

    def _kwargs(self, request: ModelRequest, *, stream: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model or self.default_model,
            "messages": self._messages(request),
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = list(request.tools)
        return payload

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_available()
        client = self._client
        if client is None:
            raise ProviderRequestError(f"Provider adapter '{self.provider}' is unavailable")
        try:
            response = client.chat.completions.create(**self._kwargs(request))
            return self._normalize(response, request.model or self.default_model)
        except Exception as exc:  # provider SDKs expose different exception types
            raise self._map_error(exc) from exc

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self._require_available()
        client = self._client
        if client is None:
            raise ProviderRequestError(f"Provider adapter '{self.provider}' is unavailable")
        try:
            response = client.chat.completions.create(**self._kwargs(request, stream=True))
            for chunk in response:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                text = getattr(delta, "content", None) if delta else None
                if text:
                    yield str(text)
        except Exception as exc:
            raise self._map_error(exc) from exc

    def _normalize(self, response: Any, model: str) -> ModelResponse:
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise ProviderResponseError(f"Provider '{self.provider}' returned no choices")
        choice = choices[0]
        message = getattr(choice, "message", None)
        text = str(getattr(message, "content", None) or "") if message else ""
        tool_calls: list[dict[str, Any]] = []
        for call in getattr(message, "tool_calls", None) or []:
            function = getattr(call, "function", None)
            if not function:
                continue
            arguments = getattr(function, "arguments", {}) or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    pass
            tool_calls.append(
                {"id": getattr(call, "id", None), "name": getattr(function, "name", ""), "arguments": arguments}
            )
        usage = getattr(response, "usage", None)
        usage_dict = {
            "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
            "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        }
        return ModelResponse(
            text=text,
            provider=self.provider,
            model=model,
            finish_reason=str(getattr(choice, "finish_reason", "stop") or "stop"),
            tool_calls=tuple(tool_calls),
            usage=usage_dict,
            request_id=getattr(response, "id", None),
            raw=response,
        )

    @staticmethod
    def _map_error(error: Exception) -> ProviderRequestError:
        status = getattr(error, "status_code", None)
        text = str(error)
        if status in (401, 403):
            return ProviderAuthenticationError("Provider authentication failed")
        if status == 429:
            return ProviderRateLimitError("Provider rate limit reached")
        return ProviderRequestError(f"Provider request failed: {text[:240]}")
