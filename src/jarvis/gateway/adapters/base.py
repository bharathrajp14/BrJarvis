"""Shared adapter mechanics; provider SDK construction stays in this package."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..contracts import ModelRequest, ModelResponse
from ..errors import AdapterUnavailableError


class BaseAdapter(ABC):
    """Provider adapter base with explicit capability filtering."""

    def __init__(
        self,
        *,
        provider: str,
        default_model: str,
        models: frozenset[str] | None = None,
        capabilities: frozenset[str] | None = None,
    ) -> None:
        self._provider = provider
        self._default_model = default_model
        self._models = models or frozenset()
        self._capabilities = capabilities or frozenset({"chat"})

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def models(self) -> frozenset[str]:
        return self._models

    @property
    def capabilities(self) -> frozenset[str]:
        return self._capabilities

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether the adapter has enough configuration to execute requests."""

    def supports(self, model: str | None, capability: str | None = None) -> bool:
        if not self.available:
            return False
        if model and self._models and model not in self._models:
            return False
        if not capability:
            return True
        from ..routing import CAPABILITY_ALIASES

        aliases = CAPABILITY_ALIASES.get(capability.lower(), {capability.lower()})
        return bool(self._capabilities & aliases)

    def _require_available(self) -> None:
        if not self.available:
            raise AdapterUnavailableError(f"Provider adapter '{self.provider}' is unavailable")

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate one normalized response."""

    @abstractmethod
    def stream(self, request: ModelRequest) -> Iterator[str]:
        """Yield normalized text chunks."""


class InMemoryAdapter(BaseAdapter):
    """Deterministic adapter used by contract tests and local smoke checks."""

    def __init__(self, responses: list[ModelResponse] | None = None) -> None:
        super().__init__(
            provider="test",
            default_model="test-model",
            models=frozenset({"test-model"}),
            capabilities=frozenset({"chat", "code", "reasoning", "vision"}),
        )
        self.responses = list(responses or [ModelResponse(text="ok", provider="test", model="test-model")])
        self.requests: list[ModelRequest] = []

    @property
    def available(self) -> bool:
        return True

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        response = (
            self.responses.pop(0) if self.responses else ModelResponse(text="ok", provider="test", model="test-model")
        )
        return response

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self.requests.append(request)
        yield from ("o", "k")
