"""Concrete provider adapters kept behind the gateway boundary."""

from __future__ import annotations

from typing import Any

from .openai import OpenAIAdapter


class ClaudeAdapter(OpenAIAdapter):
    """Claude adapter for an OpenAI-compatible Claude endpoint."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            provider="claude",
            model=kwargs.pop("model", "claude-sonnet-4-6-thinking"),
            capabilities=frozenset({"chat", "code", "reasoning", "vision"}),
            **kwargs,
        )


class GeminiAdapter(OpenAIAdapter):
    """Gemini adapter for an OpenAI-compatible Gemini endpoint."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            provider="gemini",
            model=kwargs.pop("model", "gemini-3-flash-agent"),
            capabilities=frozenset({"chat", "code", "reasoning", "vision", "image"}),
            **kwargs,
        )


class OllamaAdapter(OpenAIAdapter):
    """Local Ollama adapter with a local-only default endpoint."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            provider="ollama",
            model=kwargs.pop("model", "llama3.3"),
            base_url=kwargs.pop("base_url", "http://127.0.0.1:11434/v1"),
            api_key=kwargs.pop("api_key", "ollama"),
            capabilities=frozenset({"chat", "code", "reasoning", "vision"}),
            **kwargs,
        )

    @property
    def available(self) -> bool:
        return self._client is not None


__all__ = ["ClaudeAdapter", "GeminiAdapter", "OllamaAdapter"]
