"""
actions/_gemini_client.py — Centralized Gemini client factory for all action modules.

Routes through the local OpenAI-compatible proxy when JARVIS_ROUTE_GEMINI_TO_GATEWAY=true
(the default for this project), or falls back to direct Google Gemini API.

Usage in any action file:
    from brjarvis.actions._gemini_client import get_gemini_client, gemini_generate

    # Option A: Get client object (google.genai-style wrapper)
    client = get_gemini_client()
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)

    # Option B: One-shot generation (recommended — handles proxy automatically)
    text = gemini_generate(prompt, model="gemini-3.5-flash")
"""

from __future__ import annotations

import logging
import os
from typing import Any

from ._credentials import get_gemini_key, get_openai_key

logger = logging.getLogger("JARVIS.Actions.GeminiClient")


def _load_gemini_key() -> str:
    """Load the Gemini API key from environment or the OS credential vault."""
    return get_gemini_key()


def _load_proxy_config() -> tuple[str, str]:
    """Return (base_url, api_key) for the local OpenAI-compatible proxy."""
    base_url = (os.environ.get("BRJARVIS_PROXY_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:20128/v1").strip()
    api_key = get_openai_key()

    return base_url, api_key or "none"


def _use_proxy() -> bool:
    """Returns True if proxy routing is enabled."""
    return os.environ.get("JARVIS_ROUTE_GEMINI_TO_GATEWAY", "true").lower().strip() in {"1", "true", "yes", "on"}


# ── Proxy-aware OpenAI client wrapper that mimics google.genai API surface ──


class _ProxyGeminiClient:
    """Wraps OpenAI client to expose a google.genai-compatible interface."""

    def __init__(self, openai_client):
        self._client = openai_client
        self.models = _ProxyModels(openai_client)

    @property
    def available(self) -> bool:
        return self._client is not None


class _ProxyModels:
    def __init__(self, openai_client):
        self._client = openai_client

    def generate_content(self, model: str, contents: Any, config: dict | None = None) -> "_ProxyResponse":
        """generate_content-compatible method that routes through proxy."""
        # Normalise contents to a string prompt
        if isinstance(contents, str):
            prompt = contents
        elif isinstance(contents, list):
            parts = []
            for item in contents:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(item.get("text", str(item)))
            prompt = " ".join(parts)
        else:
            prompt = str(contents)

        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {"model": model, "messages": messages}

        # Map config options
        if config:
            max_tokens = config.get("max_output_tokens") or config.get("maxOutputTokens")
            if max_tokens:
                kwargs["max_tokens"] = int(max_tokens)
            temperature = config.get("temperature")
            if temperature is not None:
                kwargs["temperature"] = float(temperature)

        response = self._client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content or ""
        return _ProxyResponse(text)


class _ProxyResponse:
    """Minimal response wrapper matching google.genai response API."""

    def __init__(self, text: str):
        self.text = text
        self.candidates = [_ProxyCandidate(text)]


class _ProxyCandidate:
    def __init__(self, text: str):
        self.content = _ProxyContent(text)


class _ProxyContent:
    def __init__(self, text: str):
        self.parts = [_ProxyPart(text)]


class _ProxyPart:
    def __init__(self, text: str):
        self.text = text


# ── Public API ────────────────────────────────────────────────────────────────


def get_gemini_client():
    """
    Return a Gemini-compatible client, routing through proxy when enabled.

    Returns an object with:
        client.models.generate_content(model=..., contents=..., config=...)

    This is API-compatible with google.genai.Client().
    """
    if _use_proxy():
        base_url, api_key = _load_proxy_config()
        try:
            from openai import OpenAI

            oa_client = OpenAI(base_url=base_url, api_key=api_key)
            return _ProxyGeminiClient(oa_client)
        except Exception as e:
            logger.warning("Proxy client failed (%s), falling back to direct Google API", e)

    # Direct Google API fallback
    from google import genai

    return genai.Client(api_key=_load_gemini_key())


def gemini_generate(
    prompt: str | list,
    model: str = "gemini-3.5-flash",
    config: dict | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    One-shot text generation — the recommended entry point for action modules.

    Automatically routes through proxy or direct API based on env config.
    Returns the generated text string, or raises on failure.

    Args:
        prompt:     String prompt or list of content parts.
        model:      Model ID (proxy alias or real Google model name).
        config:     Optional generation config dict (temperature, max_output_tokens, etc.)
        max_tokens: Shortcut for config["max_output_tokens"].
    """
    if max_tokens:
        if config is None:
            config = {"max_output_tokens": max_tokens}
        else:
            config = {**config, "max_output_tokens": config.get("max_output_tokens", max_tokens)}

    client = get_gemini_client()
    response = client.models.generate_content(model=model, contents=prompt, config=config)
    return response.text.strip() if response.text else ""


def get_proxy_model(proxy_alias: str = "gemini-3.5-flash", real_model: str = "gemini-2.5-flash") -> str:
    """
    Return the correct model name based on whether proxy routing is active.

    Use this when an action has different proxy alias vs real API model name.

    Args:
        proxy_alias: Model ID for the local proxy (e.g. 'gemini-3.6-flash-high')
        real_model:  Real Google API model name (e.g. 'gemini-2.5-flash')
    """
    return proxy_alias if _use_proxy() else real_model
