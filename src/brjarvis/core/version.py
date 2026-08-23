# core/version.py — Canonical Version Authority for BR JARVIS
"""
Single authoritative source of version and build metadata for BR JARVIS.
All CLI banners, Web UI indicators, API responses, health endpoints, package metadata,
and runtime logs must source version information exclusively from here.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from typing import Any, Dict

try:
    __version__ = distribution_version("brjarvis")
except PackageNotFoundError:
    # Source checkouts without installed metadata still use the release value
    # declared in pyproject.toml and verified by the release checks.
    __version__ = "41.0.3"
VERSION = __version__
BUILD = "2026-08-23"
CODENAME = "MARK XLI"
DESCRIPTION = "BR JARVIS — Cognitive Multi-Modal AI Operating System & Autonomous Controller"


def get_version() -> str:
    """Return the canonical version string."""
    return VERSION


def get_version_info() -> Dict[str, Any]:
    """Return structured version and release metadata."""
    return {
        "version": VERSION,
        "build": BUILD,
        "codename": CODENAME,
        "description": DESCRIPTION,
    }


def get_banner_info() -> str:
    """Return single-line formatted version banner."""
    return f"BR JARVIS v{VERSION} ({CODENAME}, Build {BUILD})"
