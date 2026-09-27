"""Validated startup configuration for the rebuilt runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, Mapping

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigurationError
from .paths import PathLayout


class JarvisConfig(BaseSettings):
    """Single startup contract; unknown environment keys are intentionally ignored."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    assistant_name: str = "BR"
    wake_word: str = "jarvis"
    default_backend: str = "gpt"
    host: str = Field(default="127.0.0.1", validation_alias=AliasChoices("JARVIS_HOST", "BR_SERVER_HOST", "HOST"))
    port: Annotated[int, Field(ge=1, le=65535)] = Field(
        default=8000,
        validation_alias=AliasChoices("JARVIS_PORT", "BR_SERVER_PORT", "PORT"),
    )
    workspace_dir: Path | None = None
    runtime_dir: Path | None = None
    data_dir: Path | None = None
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("JARVIS_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("JARVIS_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    )
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("JARVIS_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> str:
        return str(value).strip().upper()

    @field_validator("default_backend", "assistant_name", "wake_word", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    def apply_paths(self, layout: PathLayout) -> "JarvisConfig":
        """Return a copy with path defaults resolved against the canonical layout."""
        return self.model_copy(
            update={
                "workspace_dir": self.workspace_dir or layout.workspace_root,
                "runtime_dir": self.runtime_dir or layout.runtime_root,
                "data_dir": self.data_dir or layout.data_root,
            }
        )

    def validate_startup(self) -> None:
        """Reject unsafe production configuration before any surface starts."""
        if self.environment == "production" and not any(
            (self.openai_api_key, self.anthropic_api_key, self.gemini_api_key)
        ):
            raise ConfigurationError("Production requires at least one configured model provider credential")

    def configured_providers(self) -> tuple[str, ...]:
        providers: list[str] = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.gemini_api_key:
            providers.append("gemini")
        return tuple(providers)


def load_config(
    layout: PathLayout | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> JarvisConfig:
    """Load `.env`, environment variables, and explicit overrides in that order."""
    resolved_layout = layout or PathLayout.from_project()
    env_file = resolved_layout.project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
    config = JarvisConfig(**dict(overrides or {}))
    config = config.apply_paths(resolved_layout)
    config.validate_startup()
    return config
