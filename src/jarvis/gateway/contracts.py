"""Provider-neutral request and response contracts for the rebuilt gateway."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

Message = dict[str, Any]
ToolDefinition = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """Provider-neutral model invocation request."""

    messages: tuple[Message, ...]
    model: str | None = None
    system: str | None = None
    tools: tuple[ToolDefinition, ...] = ()
    max_tokens: int | None = None
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_values(
        cls,
        messages: list[Message],
        *,
        model: str | None = None,
        system: str | None = None,
        tools: list[ToolDefinition] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        metadata: dict[str, Any] | None = None,
    ) -> "ModelRequest":
        return cls(
            messages=tuple(messages),
            model=model,
            system=system,
            tools=tuple(tools or ()),
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=dict(metadata or {}),
        )

    def with_model(self, model: str) -> "ModelRequest":
        return ModelRequest(
            messages=self.messages,
            model=model,
            system=self.system,
            tools=self.tools,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            metadata=self.metadata,
        )


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Normalized completion response returned by every provider adapter."""

    text: str
    provider: str
    model: str
    finish_reason: str = "stop"
    tool_calls: tuple[dict[str, Any], ...] = ()
    usage: dict[str, int] = field(default_factory=dict)
    request_id: str | None = None
    raw: Any = None


@runtime_checkable
class ProviderAdapter(Protocol):
    """Minimal provider adapter surface owned by the gateway."""

    @property
    def provider(self) -> str: ...

    @property
    def default_model(self) -> str: ...

    @property
    def models(self) -> frozenset[str]: ...

    @property
    def capabilities(self) -> frozenset[str]: ...

    @property
    def available(self) -> bool: ...

    def supports(self, model: str | None, capability: str | None = None) -> bool: ...

    def generate(self, request: ModelRequest) -> ModelResponse: ...

    def stream(self, request: ModelRequest) -> Iterator[str]: ...
