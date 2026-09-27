"""Pollinations media generation adapter with dynamic discovery, checksums, and artifact registration."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from ..contracts import ModelRequest, ModelResponse
from ..errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from ..quota import ProviderQuotaManager, get_quota_manager
from .base import BaseAdapter

logger = logging.getLogger("jarvis.gateway.pollinations")


@dataclass(frozen=True, slots=True)
class ImageArtifact:
    """Registered image generation artifact with integrity checksum."""

    artifact_id: str
    filepath: str
    sha256: str
    prompt: str
    model: str
    width: int
    height: int
    format: str
    size_bytes: int
    created_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


class PollinationsAdapter(BaseAdapter):
    """Production adapter for gen.pollinations.ai media generation."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://gen.pollinations.ai",
        default_model: str = "tongyi-mai/z-image-turbo",
        models: frozenset[str] | None = None,
        artifacts_dir: str | Path | None = None,
        timeout: float = 45.0,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        super().__init__(
            provider="pollinations",
            default_model=default_model,
            models=models or frozenset(),
            capabilities=frozenset({"image_generation", "image", "media_generation"}),
        )
        self._api_key = api_key or os.environ.get("POLLINATIONS_API_KEY", "")
        if not self._api_key:
            env_file = Path(__file__).resolve().parents[4] / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("POLLINATIONS_API_KEY="):
                        self._api_key = line.partition("=")[2].strip().strip('"').strip("'")
                        break

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._quota_manager = quota_manager or get_quota_manager()
        self._artifacts_dir = Path(
            artifacts_dir or Path(__file__).resolve().parents[4] / "data" / "artifacts" / "images"
        )
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._discovered_image_models: list[str] = []
        self._last_discovery_time: float = 0.0

    @property
    def available(self) -> bool:
        return bool(self._api_key) and self._quota_manager.is_available(self.provider)

    def discover_models(self, force: bool = False) -> list[str]:
        """Dynamically query /models catalog to find currently supported image models."""
        now = time.monotonic()
        if not force and self._discovered_image_models and (now - self._last_discovery_time) < 3600.0:
            return self._discovered_image_models

        url = f"{self._base_url}/models"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    img_models = [m.get("name") for m in data if m.get("category") == "image" and m.get("name")]
                    if img_models:
                        self._discovered_image_models = img_models
                        self._models = frozenset(img_models)
                        self._last_discovery_time = now
                        logger.info("[Pollinations] Discovered %d image models: %s", len(img_models), img_models[:5])
                        return img_models
        except Exception as exc:
            logger.warning("[Pollinations] Model discovery failed: %s", exc)

        # Fallback default models if dynamic discovery was not reachable
        fallback = [self.default_model, "black-forest-labs/flux.1.1-pro", "flux"]
        self._discovered_image_models = fallback
        self._models = frozenset(fallback)
        return fallback

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        width: int = 1024,
        height: int = 1024,
        aspect_ratio: str | None = None,
        seed: int | None = None,
    ) -> ImageArtifact:
        """Full image generation pipeline with download, validation, checksum, and artifact registration."""
        self._require_available()
        normalized_prompt = self._normalize_prompt(prompt)
        resolved_width, resolved_height = self._resolve_dimensions(width, height, aspect_ratio)

        # Ensure model discovery has run
        if not self._discovered_image_models:
            self.discover_models()

        chosen_model = model or (self._discovered_image_models[0] if self._discovered_image_models else self.default_model)

        self._quota_manager.record_request(self.provider, model=chosen_model, capability="image_generation")
        raw_bytes, mime_type = self._request_generation(
            prompt=normalized_prompt,
            model=chosen_model,
            width=resolved_width,
            height=resolved_height,
            seed=seed,
        )

        # Validate file integrity
        ext = self._validate_image_content(raw_bytes)
        sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # Register artifact
        artifact_id = f"img_{sha256[:12]}_{int(time.time())}"
        filename = f"{artifact_id}.{ext}"
        filepath = self._artifacts_dir / filename
        filepath.write_bytes(raw_bytes)

        metadata = {
            "prompt": normalized_prompt,
            "model": chosen_model,
            "width": resolved_width,
            "height": resolved_height,
            "seed": seed,
            "aspect_ratio": aspect_ratio,
        }

        artifact = ImageArtifact(
            artifact_id=artifact_id,
            filepath=str(filepath.resolve()),
            sha256=sha256,
            prompt=normalized_prompt,
            model=chosen_model,
            width=resolved_width,
            height=resolved_height,
            format=ext,
            size_bytes=len(raw_bytes),
            created_at=time.time(),
            metadata=metadata,
        )

        self._quota_manager.record_success(self.provider)
        logger.info("[Pollinations] Created image artifact '%s' (%d bytes, sha256=%s)", artifact_id, len(raw_bytes), sha256[:8])
        return artifact

    def _request_generation(
        self,
        *,
        prompt: str,
        model: str,
        width: int,
        height: int,
        seed: int | None = None,
    ) -> tuple[bytes, str]:
        """Attempt POST /v1/images/generations first, falling back to GET /image/{prompt}."""
        headers = {"Authorization": f"Bearer {self._api_key}"}

        # Method 1: OpenAI-compatible POST /v1/images/generations
        url_post = f"{self._base_url}/v1/images/generations"
        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json",
        }
        if seed is not None:
            payload["seed"] = seed

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url_post, headers=headers, json=payload)
                self._quota_manager.update_from_headers(self.provider, resp.headers)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", [])
                if items:
                    b64 = items[0].get("b64_json")
                    if b64:
                        return base64.b64decode(b64), "image/png"
                    url = items[0].get("url")
                    if url:
                        with httpx.Client(timeout=self._timeout) as client:
                            img_resp = client.get(url)
                            if img_resp.status_code == 200:
                                return img_resp.content, img_resp.headers.get("content-type", "image/png")
            elif resp.status_code in (401, 403):
                err = ProviderAuthenticationError(f"Pollinations authentication failure: {resp.text[:200]}")
                self._quota_manager.record_failure(self.provider, err)
                raise err
            elif resp.status_code == 429:
                err = ProviderRateLimitError(f"Pollinations rate limit exceeded: {resp.text[:200]}")
                self._quota_manager.record_failure(self.provider, err)
                raise err

        except (ProviderAuthenticationError, ProviderRateLimitError):
            raise
        except Exception as exc:
            logger.debug("[Pollinations] POST /v1/images/generations failed (%s), trying GET /image fallback", exc)

        # Method 2: GET /image/{prompt} direct binary download
        import urllib.parse

        encoded_prompt = urllib.parse.quote(prompt)
        query = f"width={width}&height={height}&model={model}"
        if seed is not None:
            query += f"&seed={seed}"
        url_get = f"{self._base_url}/image/{encoded_prompt}?{query}"

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(url_get, headers=headers)
                self._quota_manager.update_from_headers(self.provider, resp.headers)

            if resp.status_code == 200 and len(resp.content) > 1000:
                ct = resp.headers.get("content-type", "image/jpeg")
                return resp.content, ct

            raise ProviderRequestError(f"Pollinations generation failed with status {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            err = ProviderRequestError(f"Pollinations image generation error: {exc}")
            self._quota_manager.record_failure(self.provider, err)
            raise err from exc

    @staticmethod
    def _normalize_prompt(prompt: str) -> str:
        clean = " ".join(prompt.strip().split())
        return clean[:1000]

    @staticmethod
    def _resolve_dimensions(width: int, height: int, aspect_ratio: str | None) -> tuple[int, int]:
        if not aspect_ratio:
            return width, height
        ratios = {
            "1:1": (1024, 1024),
            "16:9": (1280, 720),
            "9:16": (720, 1280),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
            "3:2": (1080, 720),
            "2:3": (720, 1080),
        }
        return ratios.get(aspect_ratio, (width, height))

    @staticmethod
    def _validate_image_content(data: bytes) -> str:
        """Validate standard image magic bytes."""
        if len(data) < 8:
            raise ProviderRequestError("Generated image data is too small to be a valid image file")
        # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        # JPEG magic number: FF D8 FF
        if data[:3] == b"\xff\xd8\xff":
            return "jpg"
        # WEBP: RIFF....WEBP
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "webp"
        raise ProviderRequestError("Returned payload does not have valid image magic bytes (PNG/JPG/WEBP)")

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Adapts model request for image generation."""
        self._require_available()
        prompt = request.messages[-1].get("content", "") if request.messages else ""
        if isinstance(prompt, list):
            prompt = " ".join(item.get("text", "") for item in prompt if isinstance(item, dict))

        width = int(request.metadata.get("width", 1024))
        height = int(request.metadata.get("height", 1024))
        aspect_ratio = request.metadata.get("aspect_ratio")
        seed = request.metadata.get("seed")

        artifact = self.generate_image(
            str(prompt),
            model=request.model or self.default_model,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            seed=seed,
        )

        return ModelResponse(
            text=f"[IMAGE: {artifact.filepath} (sha256={artifact.sha256[:8]})]",
            provider=self.provider,
            model=artifact.model,
            finish_reason="stop",
            raw=artifact,
        )

    def stream(self, request: ModelRequest) -> Iterator[str]:
        resp = self.generate(request)
        yield resp.text


__all__ = ["PollinationsAdapter", "ImageArtifact"]
