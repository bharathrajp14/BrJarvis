# backends/gemini.py — JARVIS MK37 Primary AI Backend (Gemini)
"""
Robust Gemini backend — the ONLY required backend for JARVIS MK37.
Supports: text completion, streaming, vision, grounding (web search).
Falls back gracefully on any model error.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Generator

from brjarvis.core.paths import paths

from .base import BaseBackend

logger = logging.getLogger("JARVIS.GeminiBackend")


def _load_api_key() -> str:
    """Load Gemini API key from environment variable, config, or config/api_keys.json."""
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    if key:
        return key
    try:
        from brjarvis.core.config import get_config

        cfg_key = get_config().secrets.gemini_api_key
        if cfg_key and cfg_key.strip():
            return cfg_key.strip()
    except Exception:
        pass
    try:
        cfg_file = paths.CONFIG_ROOT / "api_keys.json"
        if cfg_file.exists():
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            for k, v in data.items():
                if str(k).lower().strip() in ("gemini_api_key", "google_api_key") and str(v).strip():
                    return str(v).strip()
    except Exception:
        pass
    return ""


class GeminiBackend(BaseBackend):
    """
    Full-featured Gemini backend for JARVIS MK37.
    Model priority: gemini-3.5-flash → gemini-3.1-pro-preview → ...
    """

    FALLBACK_MODELS = [
        "gemini-3.6-flash-high",
        "gemini-3-flash-agent",
        "gemini-3.7-flash-high",
        "gemini-3.6-flash-medium",
        "gemini-3.6-flash-low",
        "gemini-3.5-flash-low",
    ]

    def __init__(self, model: str = None, api_key: str = None):
        self._use_openai_client = False
        self._client = None
        self._explicit_model = model

        use_proxy = os.environ.get("JARVIS_ROUTE_GEMINI_TO_GATEWAY", "true").lower() in ("1", "true", "yes", "on")
        if use_proxy:
            try:
                from openai import OpenAI  # type: ignore

                base_url = os.environ.get("BRJARVIS_PROXY_BASE_URL") or os.environ.get(
                    "OPENAI_BASE_URL", "http://127.0.0.1:20128/v1"
                )
                api_key_val = (
                    os.environ.get("BRJARVIS_PROXY_API_KEY")
                    or os.environ.get("OPENAI_API_KEY", "sk-5ec70bf9fa324084b7a7326babf52c45").strip()
                    or "sk-5ec70bf9fa324084b7a7326babf52c45"
                )
                self._client = OpenAI(base_url=base_url, api_key=api_key_val, max_retries=1)
                self._use_openai_client = True
                self.model = model or self._pick_model()
                logger.info(f"Routed via local proxy gateway: {base_url} (model: {self.model})")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize local proxy client: {e}. Falling back to direct Google client.")

        # Standard direct Google fallback
        self.api_key = api_key or _load_api_key()
        self.model = model or self._pick_model()
        if self.api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"[OK] Using model: {self.model}")
            except Exception as ex:
                logger.warning("Failed to initialize direct Google client: %s", ex)
                self._client = None
        else:
            self._client = None
            logger.info("No direct Gemini API key provided; relying on proxy/offline.")

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def available(self) -> bool:
        return self._client is not None or getattr(self, "_genai_client", None) is not None

    def _pick_model(self) -> str:
        """Try to use the best available model."""
        try:
            from brjarvis.config.models import get_model

            cfg_model = get_model("gemini")
            if cfg_model and cfg_model != "gemini-3.5-flash":
                return cfg_model
        except Exception:
            pass
        return self.FALLBACK_MODELS[0]

    def _get_target_model(self, messages: list, system: str = "") -> str:
        if self._explicit_model:
            return self._explicit_model
        try:
            from brjarvis.config.complexity_router import select_model_for_prompt

            chosen = select_model_for_prompt(messages=messages, system=system)
            if chosen == "gemini-3.5-flash":
                return "gemini-3.6-flash-high"
            return chosen
        except Exception:
            return self.model

    @property
    def client(self):
        return self._client

    def complete(self, messages: list, system: str = "", tools: list = None, max_tokens: int = None) -> str:
        """Standard completion — used by the ReAct orchestrator with flexible token budget."""
        try:
            from brjarvis.config.complexity_router import (
                analyze_complexity,
                get_recommended_token_limit,
                prune_messages_to_fit_budget,
            )

            complexity = analyze_complexity(messages=messages, system=system)
            max_output_tokens = get_recommended_token_limit(complexity, user_max_tokens=max_tokens)
            messages = prune_messages_to_fit_budget(messages, system=system)
        except Exception:
            max_output_tokens = max_tokens or 2048

        target_model = self._get_target_model(messages, system)

        if self._use_openai_client:
            full_messages = []
            if system and system.strip():
                full_messages.append({"role": "system", "content": system.strip()})
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content")
                if content is not None:
                    if isinstance(content, str) and content.strip():
                        full_messages.append({"role": role, "content": content.strip()})
                    elif not isinstance(content, str):
                        full_messages.append({"role": role, "content": str(content)})
            if not full_messages or not any(m.get("content") for m in full_messages if m.get("role") != "system"):
                full_messages.append({"role": "user", "content": "Hello"})

            try:
                response = self._client.chat.completions.create(
                    model=target_model,
                    messages=full_messages,
                    max_tokens=max_output_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                err_str = str(e).lower()
                is_conn_error = any(
                    w in err_str for w in ("connect", "refused", "unreachable", "timed out", "timeout", "connection")
                )
                if not is_conn_error:
                    logger.warning("Model %s failed: %s — trying fallbacks...", target_model, e)
                    for fallback_mod in self.FALLBACK_MODELS:
                        try:
                            resp = self._client.chat.completions.create(
                                model=fallback_mod,
                                messages=full_messages,
                            )
                            return resp.choices[0].message.content or ""
                        except Exception:
                            continue
                logger.info("Proxy gateway unavailable (%s). Falling back to direct Google client...", e)
                try:
                    direct_key = _load_api_key()
                    from google import genai

                    direct_client = genai.Client(api_key=direct_key)
                    contents = []
                    for msg in messages:
                        role = "user" if msg.get("role") == "user" else "model"
                        c = msg.get("content")
                        if c:
                            contents.append({"role": role, "parts": [{"text": str(c)}]})
                    if not contents:
                        contents = [{"role": "user", "parts": [{"text": "Hello"}]}]
                    cfg_kwargs = {}
                    if system and system.strip():
                        cfg_kwargs["system_instruction"] = system.strip()
                    resp = direct_client.models.generate_content(
                        model="gemini-2.5-flash", contents=contents, config=cfg_kwargs if cfg_kwargs else None
                    )
                    return resp.text or ""
                except Exception as ex_direct:
                    logger.error("Gemini Direct Fallback Error: %s", ex_direct)
                    # Return error string gracefully instead of crashing ReAct loop
                    return f"ERROR: Proxy gateway ({e}) and direct Gemini fallback ({ex_direct}) both unavailable"

        # Direct Google client path
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content")
            if content is not None:
                content_str = str(content).strip() if isinstance(content, str) else str(content)
                if content_str:
                    contents.append({"role": role, "parts": [{"text": content_str}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

        config = {}
        if system and system.strip():
            config["system_instruction"] = system.strip()

        for attempt, model in enumerate(self.FALLBACK_MODELS):
            try:
                target_model = self.model if attempt == 0 else model
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=config if config else None,
                )
                try:
                    # Safety filter guard: response.text raises ValueError if blocked
                    text = response.text
                    return text or ""
                except (ValueError, AttributeError) as safety_err:
                    err_lower = str(safety_err).lower()
                    # Detect safety/recitation blocks
                    if any(k in err_lower for k in ("safety", "recitation", "block", "finish_reason")):
                        logger.warning("Gemini safety/recitation filter on %s: %s", target_model, safety_err)
                        return "I'm unable to respond to that request due to content policy restrictions."
                    # Unknown attribute error — try next model
                    logger.warning("Model %s response error: %s — trying next...", target_model, safety_err)
            except Exception as e:
                err_str = str(e).lower()
                if "quota" in err_str or "rate" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                    logger.warning("Gemini 429 rate/quota limit on %s: %s", target_model, e)
                    # Break out early to trigger router fallback to alternative provider (Claude/GPT/Ollama)
                    break
                elif "safety" in err_str or "recitation" in err_str or "block" in err_str:
                    logger.warning("Safety block on %s — trying next model", target_model)
                else:
                    logger.warning("Model %s failed: %s — trying next...", target_model, e)
                time.sleep(0.5)

        return "ERROR: Gemini API quota exceeded (429 RESOURCE_EXHAUSTED). Please wait for quota reset or switch model backend."

    def stream(self, messages: list, system: str = "") -> Generator[str, None, None]:
        """Streaming completion."""
        target_model = self._get_target_model(messages, system)
        if self._use_openai_client:
            full_messages = []
            if system and system.strip():
                full_messages.append({"role": "system", "content": system.strip()})
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content")
                if content is not None:
                    if isinstance(content, str) and content.strip():
                        full_messages.append({"role": role, "content": content.strip()})
                    elif not isinstance(content, str):
                        full_messages.append({"role": role, "content": str(content)})
            if not full_messages or not any(m.get("content") for m in full_messages if m.get("role") != "system"):
                full_messages.append({"role": "user", "content": "Hello"})

            try:
                stream_res = self._client.chat.completions.create(
                    model=target_model, messages=full_messages, stream=True
                )
                for chunk in stream_res:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                yield f"\n[Gemini Proxy Stream Error: {e}]"
                return

        # Direct Google client path
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content")
            if content is not None:
                content_str = str(content).strip() if isinstance(content, str) else str(content)
                if content_str:
                    contents.append({"role": role, "parts": [{"text": content_str}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

        config = {}
        if system and system.strip():
            config["system_instruction"] = system.strip()

        try:
            for chunk in self.client.models.generate_content_stream(
                model=target_model,
                contents=contents,
                config=config if config else None,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[Stream error: {e}]"

    def complete_with_search(self, query: str, system: str = "") -> str:
        """Completion with Google Search grounding (real-time web data)."""
        if self._use_openai_client:
            return self.complete([{"role": "user", "content": query}], system)

        # Direct path
        try:
            config = {"tools": [{"google_search": {}}]}
            if system:
                config["system_instruction"] = system

            response = self.client.models.generate_content(
                model=self.model,
                contents=query,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            logger.warning("Search grounding failed: %s — falling back to regular completion", e)
            return self.complete([{"role": "user", "content": query}], system)

    def complete_with_vision(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        """Vision completion — analyze an image."""
        if self._use_openai_client:
            import base64

            try:
                b64 = base64.b64encode(image_bytes).decode("ascii")
                data_url = f"data:{mime_type};base64,{b64}"
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ]
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                return f"Vision error: {e}"

        # Direct path
        import base64

        try:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            contents = [
                {
                    "role": "user",
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64}},
                        {"text": prompt},
                    ],
                }
            ]
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            return f"Vision error: {e}"

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio bytes using 100% Offline Local Whisper, falling back to API if offline unavailable."""
        import base64

        # 0. Prioritize 100% Offline Local Whisper (sub-30ms, no network 503 errors)
        try:
            from brjarvis.voice.whisper_local import is_available
            from brjarvis.voice.whisper_local import transcribe as whisper_transcribe

            if is_available():
                res = whisper_transcribe(audio_bytes)
                if res and res.strip():
                    return res.strip()
        except Exception:
            pass

        if self._use_openai_client and self._client:
            try:
                # 1. Try standard OpenAI whisper endpoint
                file_payload = ("audio.wav", audio_bytes, mime_type)
                try:
                    response = self._client.audio.transcriptions.create(
                        model="whisper-1",
                        file=file_payload,
                    )
                    return (response.text or "").strip()
                except Exception:
                    # 2. Multimodal Chat Fallback for proxy gateways returning HTTP 415/503
                    b64 = base64.b64encode(audio_bytes).decode("ascii")
                    try:
                        resp = self._client.chat.completions.create(
                            model=self.model or "gemini-2.5-flash",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Transcribe this audio clip exactly. Return only the transcription, no intro, no comments.",
                                        },
                                        {"type": "image_url", "image_url": {"url": f"data:audio/wav;base64,{b64}"}},
                                    ],
                                }
                            ],
                        )
                        return (resp.choices[0].message.content or "").strip()
                    except Exception:
                        return ""
            except Exception as e:
                logger.warning("GeminiBackend Transcription error: %s", e)
                return ""

        # Direct Google Gemini API path
        try:
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            contents = [
                {
                    "role": "user",
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64}},
                        {
                            "text": "Transcribe this audio clip exactly. Output only the transcription, no intro, no comments."
                        },
                    ],
                }
            ]

            target_client = getattr(self, "_client", None) or getattr(self, "client", None)
            if target_client:
                # 1. google.genai Client v1.0+ (client.models.generate_content is callable)
                models_attr = getattr(target_client, "models", None)
                if models_attr and callable(getattr(models_attr, "generate_content", None)):
                    response = models_attr.generate_content(
                        model=self.model or "gemini-2.0-flash",
                        contents=contents,
                    )
                    return (response.text or "").strip()
                # 2. Direct model or legacy generativeai instance (client.generate_content is callable)
                elif callable(getattr(target_client, "generate_content", None)):
                    response = target_client.generate_content(contents)
                    return (response.text or "").strip()

            # 3. Direct google.genai Client fallback
            try:
                from google import genai

                key = getattr(self, "api_key", None) or _load_api_key()
                g_client = genai.Client(api_key=key)
                response = g_client.models.generate_content(
                    model=self.model or "gemini-2.0-flash",
                    contents=contents,
                )
                return (response.text or "").strip()
            except Exception:
                pass
        except Exception as e:
            logger.warning("Gemini Direct Transcription failed: %s", e)

        return ""

    def quick(self, prompt: str) -> str:
        """Quick single-prompt completion — for planning, routing, etc."""
        return self.complete([{"role": "user", "content": prompt}])

    def ping(self, timeout: float = 30.0) -> bool:
        """Health check via completion to leverage fallback model chain."""
        try:
            start = time.monotonic()
            result = self.complete([{"role": "user", "content": "ping"}])
            elapsed = time.monotonic() - start
            is_err = "error" in result.lower() or "failed" in result.lower()
            return bool(result) and not is_err and elapsed < timeout
        except Exception:
            return False
