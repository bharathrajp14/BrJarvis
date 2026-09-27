# backends/openai_compat.py — JARVIS MK37 OpenAI-Compatible Backend
"""
OpenAI-compatible backend connector for BR Core.
Delegates to the centralized ModelGateway pointing to Proxy Brain (default: http://localhost:8045/v1).
"""

from __future__ import annotations

import logging
import os
from typing import Generator

from brjarvis.gateway.model_gateway import ModelGateway

from .base import BaseBackend

logger = logging.getLogger("JARVIS.OpenAI")


class OpenAIBackend(BaseBackend):
    """OpenAI-compatible backend adapter wrapping the centralized ModelGateway."""

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        self._explicit_model = model or os.environ.get("OPENAI_MODEL", "").strip() or None
        default_model = "gpt-4o-mini"
        try:
            from brjarvis.core.config import get_config

            default_model = get_config().models.gpt or default_model
        except Exception:
            pass
        self.model = self._explicit_model or default_model
        self._gateway = ModelGateway(base_url=base_url, api_key=api_key)

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_local(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        has_key = bool(self._gateway.api_key and self._gateway.api_key not in ("none", "local-proxy-brain"))
        has_proxy = bool(os.environ.get("OPENAI_BASE_URL") or os.environ.get("BRJARVIS_PROXY_BASE_URL"))
        return has_key or has_proxy or bool(os.environ.get("OPENAI_API_KEY"))

    def complete(self, messages: list, system: str = "", tools: list = None, max_tokens: int = None) -> str:
        # Fast fail if pointing to localhost proxy that is not running
        if any(p in self._gateway.base_url for p in ("localhost:8045", "127.0.0.1:8045", "localhost:20128", "127.0.0.1:20128")) and not bool(
            os.environ.get("OPENAI_API_KEY", "").startswith("sk-proj-")
        ):
            if not self._gateway.ping(timeout=0.3):
                return f"ERROR: Local Proxy Brain ({self._gateway.base_url}) is offline. Bypassing proxy for cloud fallback."
        try:
            resp = self._gateway.complete(
                messages=messages, model=self.model, system=system, tools=tools, max_tokens=max_tokens
            )
            return resp.text
        except Exception as e:
            logger.warning("[OpenAI] Completion notice: %s", e)
            return f"ERROR: {e}"

    def stream(self, messages: list, system: str = "", max_tokens: int = None) -> Generator[str, None, None]:
        try:
            yield from self._gateway.stream(messages=messages, model=self.model, system=system, max_tokens=max_tokens)
        except Exception as e:
            yield f"[OpenAI Stream Error: {e}]"
