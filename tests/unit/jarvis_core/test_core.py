from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from jarvis.core.bootstrap import build_assistant_runtime, reset_assistant_runtime, run_doctor
from jarvis.core.config import JarvisConfig, load_config
from jarvis.core.di import Container
from jarvis.core.errors import ConfigurationError
from jarvis.core.lifecycle import Lifecycle
from jarvis.core.paths import PathLayout, PathLayoutError


@pytest.fixture(autouse=True)
def reset_runtime() -> Generator[None, None, None]:
    reset_assistant_runtime()
    yield
    reset_assistant_runtime()


def test_container_singleton_and_transient_contract() -> None:
    class Service:
        pass

    container = Container()
    container.register_singleton(Service, Service)
    assert container.resolve(Service) is container.resolve(Service)

    container.register_transient(Service, Service)
    assert container.resolve(Service) is not container.resolve(Service)


def test_workspace_paths_are_contained(tmp_path: Path) -> None:
    layout = PathLayout.from_project(tmp_path)
    layout.ensure_directories()
    assert layout.resolve_workspace("notes/today.md") == layout.workspace_root / "notes" / "today.md"
    with pytest.raises(PathLayoutError):
        layout.resolve_workspace("../outside.txt")


def test_config_loads_environment_and_resolves_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    layout = PathLayout.from_project(tmp_path)
    monkeypatch.setenv("JARVIS_PORT", "8123")
    config = load_config(layout, {"environment": "testing"})
    assert config.port == 8123
    assert config.environment == "testing"
    assert config.workspace_dir == layout.workspace_root
    assert config.data_dir == layout.data_root


def test_production_requires_a_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (
        "JARVIS_OPENAI_API_KEY",
        "OPENAI_API_KEY",
        "JARVIS_ANTHROPIC_API_KEY",
        "ANTHROPIC_API_KEY",
        "JARVIS_GEMINI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(variable, raising=False)
    config = JarvisConfig(environment="production")
    with pytest.raises(ConfigurationError):
        config.validate_startup()


@pytest.mark.asyncio
async def test_lifecycle_runs_shutdown_hooks_in_reverse_order() -> None:
    events: list[str] = []
    lifecycle = Lifecycle()
    lifecycle.add_shutdown_hook(lambda: events.append("first"))

    async def second() -> None:
        events.append("second")

    lifecycle.add_shutdown_hook(second)
    await lifecycle.shutdown()
    await lifecycle.shutdown()
    assert events == ["second", "first"]


def test_bootstrap_creates_one_runtime_and_doctor_report(tmp_path: Path) -> None:
    layout = PathLayout.from_project(tmp_path)
    config = JarvisConfig(environment="testing")
    first = build_assistant_runtime(config=config, layout=layout)
    second = build_assistant_runtime()
    assert first is second
    report = run_doctor()
    assert report["runtime"] == "healthy"
    directories = report["directories"]
    assert isinstance(directories, dict)
    assert all(bool(value) for value in directories.values())
