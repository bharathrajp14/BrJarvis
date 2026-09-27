"""Lifecycle hooks for deterministic runtime startup and shutdown."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable

Hook = Callable[[], object | Awaitable[object]]


class Lifecycle:
    """Execute shutdown hooks in reverse registration order, once only."""

    def __init__(self) -> None:
        self._shutdown_hooks: list[Hook] = []
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def add_shutdown_hook(self, hook: Hook) -> None:
        if self._closed:
            raise RuntimeError("Cannot register a shutdown hook after lifecycle closure")
        self._shutdown_hooks.append(hook)

    async def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        for hook in reversed(self._shutdown_hooks):
            result = hook()
            if inspect.isawaitable(result):
                await result

    def reset(self) -> None:
        """Reset the lifecycle for isolated tests."""
        self._shutdown_hooks.clear()
        self._closed = False
