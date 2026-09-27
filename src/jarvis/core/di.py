"""Minimal thread-safe dependency container for the rebuilt runtime."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    """Register instances or lazy singleton/transient factories by type."""

    def __init__(self) -> None:
        self._instances: dict[type[Any], Any] = {}
        self._singletons: dict[type[Any], Callable[[], Any]] = {}
        self._transients: dict[type[Any], Callable[[], Any]] = {}
        self._singleton_cache: dict[type[Any], Any] = {}
        self._lock = RLock()

    def register_instance(self, interface: type[T], instance: T) -> None:
        with self._lock:
            self._instances[interface] = instance
            self._singletons.pop(interface, None)
            self._transients.pop(interface, None)
            self._singleton_cache.pop(interface, None)

    def register_singleton(self, interface: type[T], factory: Callable[[], T]) -> None:
        with self._lock:
            self._instances.pop(interface, None)
            self._transients.pop(interface, None)
            self._singleton_cache.pop(interface, None)
            self._singletons[interface] = factory

    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> None:
        with self._lock:
            self._instances.pop(interface, None)
            self._singletons.pop(interface, None)
            self._singleton_cache.pop(interface, None)
            self._transients[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        with self._lock:
            if interface in self._instances:
                return self._instances[interface]
            if interface in self._transients:
                return self._transients[interface]()
            if interface in self._singletons:
                if interface not in self._singleton_cache:
                    self._singleton_cache[interface] = self._singletons[interface]()
                return self._singleton_cache[interface]
        raise KeyError(f"No registration found for {interface!r}")

    def is_registered(self, interface: type[Any]) -> bool:
        with self._lock:
            return interface in self._instances or interface in self._singletons or interface in self._transients

    def registered_types(self) -> tuple[str, ...]:
        with self._lock:
            types = set(self._instances) | set(self._singletons) | set(self._transients)
            return tuple(sorted(item.__name__ for item in types))

    def clear(self) -> None:
        with self._lock:
            self._instances.clear()
            self._singletons.clear()
            self._transients.clear()
            self._singleton_cache.clear()
