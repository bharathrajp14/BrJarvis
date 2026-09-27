from __future__ import annotations

from collections.abc import Iterator

import pytest

from jarvis.gateway import (
    ModelGateway,
    ModelRequest,
    ModelResponse,
    NoRouteAvailableError,
    RoutePolicy,
    build_configured_gateway,
)
from jarvis.gateway.adapters.base import BaseAdapter


class FakeAdapter(BaseAdapter):
    def __init__(
        self,
        provider: str,
        *,
        model: str = "model",
        capabilities: frozenset[str] | None = None,
        text: str = "ok",
        fail_generate: bool = False,
        stream_chunks: tuple[str, ...] = ("ok",),
        fail_stream_after: int | None = None,
        available: bool = True,
    ) -> None:
        super().__init__(
            provider=provider,
            default_model=model,
            models=frozenset({model}),
            capabilities=capabilities or frozenset({"chat"}),
        )
        self.text = text
        self.fail_generate = fail_generate
        self.stream_chunks = stream_chunks
        self.fail_stream_after = fail_stream_after
        self._available = available
        self.requests: list[ModelRequest] = []

    @property
    def available(self) -> bool:
        return self._available

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if self.fail_generate:
            raise RuntimeError(f"{self.provider} failed")
        return ModelResponse(text=self.text, provider=self.provider, model=request.model or self.default_model)

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self.requests.append(request)
        for index, chunk in enumerate(self.stream_chunks):
            if self.fail_stream_after is not None and index >= self.fail_stream_after:
                raise RuntimeError(f"{self.provider} stream failed")
            yield chunk


def test_priority_route_and_capability_filtering() -> None:
    gateway = ModelGateway(
        {
            "local": FakeAdapter("local", capabilities=frozenset({"chat"})),
            "cloud": FakeAdapter("cloud", capabilities=frozenset({"chat", "code"})),
        },
        policies=[RoutePolicy(name="default", providers=("local", "cloud"))],
        router=None,
    )
    assert gateway.route(policy="default").candidates == ("local", "cloud")
    assert gateway.route(policy="default", capability="code").candidates == ("cloud",)


def test_generate_uses_normalized_request_and_fails_over() -> None:
    local = FakeAdapter("local", fail_generate=True)
    cloud = FakeAdapter("cloud", text="cloud answer")
    gateway = ModelGateway(
        {"local": local, "cloud": cloud},
        policies=[RoutePolicy(name="default", providers=("local", "cloud"))],
    )

    response = gateway.generate(
        [{"role": "user", "content": "hello"}],
        system="be concise",
        tools=[{"type": "function", "function": {"name": "lookup"}}],
    )

    assert response.text == "cloud answer"
    assert response.provider == "cloud"
    assert local.requests[0].system == "be concise"
    assert local.requests[0].tools[0]["type"] == "function"
    assert gateway.router.state("local").failures == 1
    assert gateway.router.state("cloud").successes == 1


def test_stream_retries_after_mid_stream_failure() -> None:
    first = FakeAdapter("first", stream_chunks=("partial", "lost"), fail_stream_after=1)
    second = FakeAdapter("second", stream_chunks=("fallback",))
    gateway = ModelGateway(
        {"first": first, "second": second},
        policies=[RoutePolicy(name="default", providers=("first", "second"))],
    )

    assert list(gateway.stream([{"role": "user", "content": "stream"}])) == ["partial", "fallback"]
    assert gateway.router.state("first").failures == 1
    assert gateway.router.state("second").successes == 1


def test_round_robin_route_cycles() -> None:
    gateway = ModelGateway(
        {"a": FakeAdapter("a"), "b": FakeAdapter("b")},
        policies=[RoutePolicy(name="cycle", strategy="round_robin", providers=("a", "b"))],
    )
    assert gateway.route(policy="cycle").selected_provider == "a"
    assert gateway.route(policy="cycle").selected_provider == "b"
    assert gateway.route(policy="cycle").selected_provider == "a"


def test_catalogue_factory_builds_a_default_route(tmp_path) -> None:
    config = tmp_path / "models.yaml"
    config.write_text(
        """proxy:\n  base_url: http://127.0.0.1:9999/v1\n  api_key_env: OPENAI_API_KEY\nrouting:\n  default_model: first\n  fallback_hierarchy: [first, second]\n  capabilities:\n    code: first\n""",
        encoding="utf-8",
    )
    gateway = build_configured_gateway(config)
    decision = gateway.route(capability="code")
    assert decision.selected_provider == "first"
    assert decision.model == "first"
    assert decision.candidates == ("first",)


def test_no_route_for_unavailable_adapter() -> None:
    gateway = ModelGateway(
        {"offline": FakeAdapter("offline", available=False)},
        policies=[RoutePolicy(name="default", providers=("offline",))],
    )
    with pytest.raises(NoRouteAvailableError):
        gateway.route()
