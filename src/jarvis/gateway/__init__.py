"""Canonical provider gateway for the BrJarvis rebuild."""

from .contracts import Message, ModelRequest, ModelResponse, ProviderAdapter, ToolDefinition
from .errors import (
    AdapterUnavailableError,
    GatewayError,
    NoRouteAvailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
)
from .factory import build_configured_gateway
from .model_gateway import ModelGateway
from .routing import CircuitState, RouteDecision, RoutePolicy, Router

__all__ = [
    "ModelGateway",
    "build_configured_gateway",
    "ModelRequest",
    "ModelResponse",
    "Message",
    "ToolDefinition",
    "ProviderAdapter",
    "RouteDecision",
    "RoutePolicy",
    "CircuitState",
    "Router",
    "GatewayError",
    "AdapterUnavailableError",
    "NoRouteAvailableError",
    "ProviderAuthenticationError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "ProviderResponseError",
]
