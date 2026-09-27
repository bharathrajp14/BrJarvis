"""Canonical filesystem layout for the rebuilt runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class PathLayoutError(ValueError):
    """Raised when a path escapes the configured project or workspace root."""


def find_project_root(start: Path | None = None) -> Path:
    """Find the repository root without depending on the old brjarvis package."""
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").exists() or (directory / ".git").exists():
            return directory
    return candidate


@dataclass(frozen=True, slots=True)
class PathLayout:
    """Stable roots used by every new subsystem."""

    project_root: Path
    config_root: Path
    runtime_root: Path
    workspace_root: Path
    data_root: Path

    @classmethod
    def from_project(cls, project_root: Path | None = None) -> "PathLayout":
        root = (project_root or find_project_root()).resolve()
        runtime_root = Path(os.environ.get("JARVIS_RUNTIME_DIR", root / "runtime")).expanduser().resolve()
        workspace_root = Path(os.environ.get("JARVIS_WORKSPACE_DIR", root / "workspace")).expanduser().resolve()
        data_root = Path(os.environ.get("JARVIS_DATA_DIR", root / ".jarvis")).expanduser().resolve()
        return cls(
            project_root=root,
            config_root=root / "config",
            runtime_root=runtime_root,
            workspace_root=workspace_root,
            data_root=data_root,
        )

    def ensure_directories(self) -> None:
        for path in (self.config_root, self.runtime_root, self.workspace_root, self.data_root):
            path.mkdir(parents=True, exist_ok=True)

    def resolve_workspace(self, relative: str | Path = ".") -> Path:
        """Resolve a workspace path and reject traversal outside its root."""
        target = (self.workspace_root / relative).resolve()
        try:
            target.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PathLayoutError(f"Workspace path escapes root: {relative}") from exc
        return target


paths = PathLayout.from_project()
