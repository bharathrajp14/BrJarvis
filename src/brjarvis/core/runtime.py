# core/runtime.py — Master ApplicationRuntime for BR JARVIS
from __future__ import annotations

import logging
import threading
from typing import Any, Optional

from brjarvis.events.bus import EventBus, get_event_bus
from brjarvis.events.types import SystemEvent

from .config import JarvisConfig, get_config
from .di import Container, get_container
from .health import HealthMonitor
from .lifecycle import LifecycleManager
from .logging import setup_logger
from .process import ProcessSupervisor

logger = logging.getLogger("JARVIS.Runtime")


class ApplicationRuntime:
    """Master Canonical Application Runtime for BR JARVIS.

    Coordinates the entire AI operating system runtime:
    - Configuration (JarvisConfig)
    - EventBus (system telemetry and async pub/sub)
    - Lifecycle & Supervision
    - Model Gateway & Capability Router
    - Cognitive Engine (Orchestrator / Agent)
    - Tool Runtime & Registries
    - Unified Memory Architecture
    - Security & Guardian Safety Core
    - Multimodal Pipelines (Voice & Vision)
    """

    def __init__(self, config: Optional[JarvisConfig] = None, *, use_vector_memory: bool = True):
        self.config: JarvisConfig = config or get_config()
        self.logger: logging.Logger = setup_logger(
            name="JARVIS",
            level=self.config.system.log_level,
            log_to_file=True,
        )
        self.container: Container = get_container()
        self.lifecycle: LifecycleManager = LifecycleManager()
        self.supervisor: ProcessSupervisor = ProcessSupervisor()
        self.health: HealthMonitor = HealthMonitor()
        self.event_bus: EventBus = get_event_bus()

        # Lazy-initialized subsystem references
        self._router: Optional[Any] = None
        self._orchestrator: Optional[Any] = None
        self._gateway: Optional[Any] = None
        self._memory: Optional[Any] = None
        self._tool_runtime: Optional[Any] = None
        self._guardian: Optional[Any] = None
        self._security: Optional[Any] = None
        self._use_vector_memory = use_vector_memory

        # Register core instances in DI container
        self.container.register_instance(ApplicationRuntime, self)
        self.container.register_instance(JarvisConfig, self.config)
        self.container.register_instance(LifecycleManager, self.lifecycle)
        self.container.register_instance(ProcessSupervisor, self.supervisor)
        self.container.register_instance(HealthMonitor, self.health)
        self.container.register_instance(EventBus, self.event_bus)

        self.logger.info(
            f"⚡ BR JARVIS ApplicationRuntime Initialized for '{self.config.assistant.name}' "
            f"(Platform: {self.config.system.environment})"
        )

    @property
    def router(self) -> Any:
        if self._router is None:
            from brjarvis.router import AgentRouter, load_available_backends

            backends = load_available_backends()
            self._router = AgentRouter(backends)
            self.container.register_instance(AgentRouter, self._router)
        return self._router

    @property
    def orchestrator(self) -> Any:
        if self._orchestrator is None:
            from brjarvis.orchestrator import JarvisOrchestrator

            self._orchestrator = JarvisOrchestrator(
                self.router,
                use_vector_memory=self._use_vector_memory,
                gateway=self.gateway,
            )

            self.container.register_instance(JarvisOrchestrator, self._orchestrator)

            # Register orchestrator shutdown hook
            async def _orch_shutdown():
                try:
                    if hasattr(self._orchestrator, "shutdown"):
                        self._orchestrator.shutdown()
                except Exception as exc:
                    self.logger.warning("Error during orchestrator shutdown: %s", exc)

            self.lifecycle.add_shutdown_hook(_orch_shutdown)
        return self._orchestrator

    @property
    def gateway(self) -> Any:
        if self._gateway is None:
            try:
                from jarvis.gateway.factory import build_configured_gateway

                self._gateway = build_configured_gateway()
                self.container.register_instance(type(self._gateway), self._gateway)
            except Exception as exc:
                self.logger.debug("Canonical ModelGateway init notice: %s", exc)
        return self._gateway

    @property
    def tool_runtime(self) -> Any:
        if self._tool_runtime is None:
            try:
                from brjarvis.tools.tool_runtime import ToolRuntime

                self._tool_runtime = ToolRuntime()
            except Exception as e:
                self.logger.debug("ToolRuntime init notice: %s", e)
        return self._tool_runtime

    @property
    def memory(self) -> Any:
        if self._memory is None:
            try:
                from brjarvis.memory.unified_memory import UnifiedMemoryManager

                self._memory = UnifiedMemoryManager()
            except Exception as e:
                self.logger.debug("UnifiedMemoryManager init notice: %s", e)
        return self._memory

    @property
    def security(self) -> Any:
        if self._security is None:
            try:
                from brjarvis.security.policy_engine import SecurityPolicyEngine

                self._security = SecurityPolicyEngine()
            except Exception as e:
                self.logger.debug("SecurityPolicyEngine init notice: %s", e)
        return self._security

    @property
    def guardian(self) -> Any:
        if self._guardian is None:
            try:
                from brjarvis.guardian.core import GuardianCore

                self._guardian = GuardianCore()
            except Exception as e:
                self.logger.debug("GuardianCore init notice: %s", e)
        return self._guardian

    @property
    def voice(self) -> Any:
        try:
            from brjarvis.voice.assistant import get_voice_assistant

            return get_voice_assistant()
        except Exception as e:
            self.logger.debug("VoiceAssistant init notice: %s", e)
            return None

    @property
    def vision(self) -> Any:
        try:
            from brjarvis.vision.engine import get_vision_engine

            return get_vision_engine()
        except Exception as e:
            self.logger.debug("VisionEngine init notice: %s", e)
            return None

    @property
    def multimodal(self) -> dict[str, Any]:
        return {
            "voice": self.voice,
            "vision": self.vision,
        }

    @property
    def observability(self) -> dict[str, Any]:
        return {
            "health": self.health,
            "supervisor": self.supervisor,
            "event_bus": self.event_bus,
        }

    async def boot(self) -> None:
        """Boot the master runtime and publish system startup event."""
        _ = self.orchestrator
        await self.lifecycle.startup()
        from brjarvis.core.version import VERSION

        self.event_bus.publish(
            SystemEvent(topic="system.startup", state="RUNNING", payload={"version": VERSION, "status": "ONLINE"})
        )

    async def shutdown(self) -> None:
        """Cleanly shutdown all subsystems."""
        self.event_bus.publish(SystemEvent(topic="system.shutdown", state="STOPPING", payload={}))
        await self.lifecycle.shutdown()


# CoreRuntime alias for backward compatibility
CoreRuntime = ApplicationRuntime

# ── Thread-safe singleton ─────────────────────────────────────────────────────
_global_runtime: Optional[ApplicationRuntime] = None
_runtime_lock = threading.Lock()


def get_runtime(*, use_vector_memory: bool = True) -> ApplicationRuntime:
    """Return the global ApplicationRuntime singleton (thread-safe)."""
    global _global_runtime
    if _global_runtime is not None:
        return _global_runtime

    with _runtime_lock:
        if _global_runtime is None:
            _global_runtime = ApplicationRuntime(use_vector_memory=use_vector_memory)
    return _global_runtime


def reset_runtime() -> None:
    """Reset the global runtime singleton (for testing only)."""
    global _global_runtime
    with _runtime_lock:
        _global_runtime = None
