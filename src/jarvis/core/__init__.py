"""Small, dependency-light composition core for the rebuilt runtime."""

from .bootstrap import AssistantRuntime, build_assistant_runtime, reset_assistant_runtime, run_doctor
from .config import JarvisConfig, load_config
from .di import Container
from .errors import ConfigurationError, JarvisError, TaskExecutionDiagnostic
from .lifecycle import Lifecycle
from .paths import PathLayout

__all__ = [
    "AssistantRuntime",
    "build_assistant_runtime",
    "reset_assistant_runtime",
    "run_doctor",
    "JarvisConfig",
    "load_config",
    "Container",
    "ConfigurationError",
    "JarvisError",
    "TaskExecutionDiagnostic",
    "Lifecycle",
    "PathLayout",
]
