# src/brjarvis/core/paths.py — Canonical Centralized Path Engine for BR JARVIS MK40.2+
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class PathContainmentError(ValueError):
    """
    Raised when a resolved path falls outside the allowed workspace root,
    or when a path contains a duplicated root segment (the workspace/workspace/ bug).
    """

    pass


def find_project_root() -> Path:
    """Deterministically locate the root directory of the BR JARVIS repository."""
    if os.environ.get("JARVIS_PROJECT_ROOT"):
        p = Path(os.environ["JARVIS_PROJECT_ROOT"]).resolve()
        if p.exists():
            return p

    curr = Path(__file__).resolve().parent
    for parent in [curr] + list(curr.parents):
        # Installed wheels live under site-packages; never treat that tree as
        # the project root or runtime data will be written into the venv.
        if "site-packages" in parent.parts:
            continue
        has_pyproject = (parent / "pyproject.toml").exists()
        has_start = (parent / "start.py").exists()
        has_src = (parent / "src" / "brjarvis").is_dir()
        if has_src and (has_pyproject or has_start or (parent / ".git").exists()):
            return parent
        if has_pyproject and has_start:
            return parent

    data_home = os.environ.get("JARVIS_DATA_DIR")
    if data_home:
        return Path(data_home).expanduser().resolve()
    return Path.home() / ".brjarvis"


def find_python_executable(root: Optional[Path] = None) -> Path:
    """
    Deterministically resolve the canonical Python interpreter with precedence:
      1. BR_JARVIS_PYTHON environment override
      2. Project .venv (PROJECT_ROOT/.venv/Scripts/python.exe on Windows, bin/python on POSIX)
      3. Repository-local virtualenv/interpreters
      4. sys.executable
    """
    import sys

    if os.environ.get("BR_JARVIS_PYTHON"):
        override = Path(os.environ["BR_JARVIS_PYTHON"]).resolve()
        if override.exists():
            return override

    proj_root = root or find_project_root()
    venv_dir = proj_root / ".venv"
    if venv_dir.exists():
        if sys.platform == "win32":
            candidates = [
                venv_dir / "Scripts" / "python.exe",
                venv_dir / "python.exe",
            ]
        else:
            candidates = [
                venv_dir / "bin" / "python3",
                venv_dir / "bin" / "python",
            ]
        for cand in candidates:
            if cand.exists():
                return cand.resolve()

    return Path(sys.executable).resolve()


def ensure_canonical_python() -> None:
    """
    If the current process was started with a non-project Python interpreter
    (e.g. system Python 3.14 instead of the project .venv Python 3.12),
    automatically re-exec with the project .venv interpreter to guarantee
    clean runtime isolation and prevent user-site package pollution.
    """
    import subprocess
    import sys

    # Skip re-exec when running inside pytest or test runners
    if (
        "pytest" in sys.modules
        or os.environ.get("JARVIS_TEST_MODE") == "true"
        or any("pytest" in a.lower() for a in sys.argv)
    ):
        return

    target = find_python_executable()
    current = Path(sys.executable).resolve()
    if target.exists() and target != current:
        if os.environ.get("_BR_JARVIS_REEXEC") != "1":
            env = os.environ.copy()
            env["_BR_JARVIS_REEXEC"] = "1"
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            cmd = [str(target)] + sys.argv
            try:
                res = subprocess.run(cmd, env=env)
                sys.exit(res.returncode)
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as _e:
                print(f"[Warning] Canonical python re-exec note: {_e}", file=sys.stderr)


class PathManager:
    """Canonical Path Contract and Workspace Lifecycle Manager for BR JARVIS MK40.2+."""

    _instance: Optional[PathManager] = None

    def __init__(self, root: Optional[Path] = None):
        self.PROJECT_ROOT = (root or find_project_root()).resolve()
        self.PYTHON_EXECUTABLE = find_python_executable(self.PROJECT_ROOT)
        self.VENV_DIR = self.PROJECT_ROOT / ".venv"
        self.DOTENV_FILE = self.PROJECT_ROOT / ".env"
        self.SOURCE_ROOT = self.PROJECT_ROOT / "src" / "brjarvis"
        self.APPS_ROOT = self.PROJECT_ROOT / "apps"
        self.CONFIG_ROOT = self.PROJECT_ROOT / "config"
        self.DOCS_ROOT = self.PROJECT_ROOT / "docs"
        self.TEST_ROOT = self.PROJECT_ROOT / "tests"
        self.SCRIPTS_ROOT = self.PROJECT_ROOT / "scripts"
        self.ASSETS_ROOT = self.PROJECT_ROOT / "assets"

        # Runtime Data Directories
        runtime_env = os.environ.get("JARVIS_RUNTIME_DIR")
        self.RUNTIME_ROOT = Path(runtime_env).resolve() if runtime_env else (self.PROJECT_ROOT / "runtime")
        self.ARTIFACT_ROOT = self.RUNTIME_ROOT / "artifacts"
        self.LOG_ROOT = Path(os.environ.get("JARVIS_LOG_DIR", str(self.RUNTIME_ROOT / "logs"))).resolve()
        self.CAPTURE_ROOT = self.RUNTIME_ROOT / "captures"
        self.REPORT_ROOT = self.RUNTIME_ROOT / "reports"
        self.TEMP_ROOT = self.RUNTIME_ROOT / "temporary"
        self.STATE_ROOT = self.RUNTIME_ROOT / "state"
        self.MEMORY_ROOT = self.STATE_ROOT / "memory_db"

        # User Workspace Directories
        ws_env = os.environ.get("JARVIS_WORKSPACE_DIR")
        self.WORKSPACE_ROOT = Path(ws_env).resolve() if ws_env else (self.PROJECT_ROOT / "workspace")
        self.DOCUMENTS_DIR = self.WORKSPACE_ROOT / "documents"
        self.RESUMES_DIR = self.WORKSPACE_ROOT / "resumes"
        self.CAREER_DIR = self.WORKSPACE_ROOT / "career"
        self.PROJECTS_DIR = self.WORKSPACE_ROOT / "projects"
        self.USER_DATA_DIR = self.WORKSPACE_ROOT / "user-data"

        # Backward compatibility aliases
        self.BASE_DIR = self.PROJECT_ROOT
        self.WORKSPACE_DIR = self.WORKSPACE_ROOT
        self.LOGS_DIR = self.LOG_ROOT
        self.CAPTURES_DIR = self.CAPTURE_ROOT
        self.ARTIFACTS_DIR = self.ARTIFACT_ROOT
        self.PID_FILE = self.STATE_ROOT / ".jarvis.pid"

        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure all required runtime and workspace directories exist."""
        for d in (
            self.RUNTIME_ROOT,
            self.ARTIFACT_ROOT,
            self.LOG_ROOT,
            self.CAPTURE_ROOT,
            self.REPORT_ROOT,
            self.TEMP_ROOT,
            self.STATE_ROOT,
            self.MEMORY_ROOT,
            self.WORKSPACE_ROOT,
            self.DOCUMENTS_DIR,
            self.RESUMES_DIR,
            self.CAREER_DIR,
            self.PROJECTS_DIR,
            self.USER_DATA_DIR,
        ):
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> PathManager:
        if cls._instance is None:
            cls._instance = PathManager()
        return cls._instance


def get_path_manager() -> PathManager:
    return PathManager.get_instance()


paths = get_path_manager()


# ── WorkspaceManager ─ canonical path resolver for all tools ───────────────


class WorkspaceManager:
    """
    Single canonical source of truth for all workspace paths in BR JARVIS.

    MK40.2 §11 / §12: All tools must use this manager. No tool may independently
    construct workspace/workspace/... paths.

    Provides:
        project_root     — root of the git repository
        workspace_root   — user-facing file vault
        documents_root   — Documents subfolder
        artifacts_root   — runtime artifacts
        career_root      — career documents
        temporary_root   — ephemeral temp files (cleaned at startup)

    All path-resolution goes through resolve_workspace_path() which:
        1. Normalises the path
        2. Rejects paths with duplicated root segments
        3. Enforces containment inside workspace_root
        4. Creates the parent directory if needed (opt-in)
    """

    _instance: Optional["WorkspaceManager"] = None

    def __init__(self, pm: Optional[PathManager] = None):
        pm = pm or get_path_manager()
        self.project_root = pm.PROJECT_ROOT
        self.workspace_root = pm.WORKSPACE_ROOT
        self.documents_root = pm.DOCUMENTS_DIR
        self.artifacts_root = pm.ARTIFACT_ROOT
        self.career_root = pm.CAREER_DIR
        self.temporary_root = pm.TEMP_ROOT

    @classmethod
    def get_instance(cls) -> "WorkspaceManager":
        if cls._instance is None:
            cls._instance = WorkspaceManager()
        return cls._instance

    def resolve_workspace_path(
        self,
        user_path: str | Path,
        create_parents: bool = False,
    ) -> Path:
        """
        Resolve a user-supplied path to a canonical absolute path inside workspace_root.

        Rules:
            - Absolute paths are taken as-is after normalisation
            - Relative paths are resolved relative to workspace_root
            - Paths must not traverse outside workspace_root (.. attacks)
            - Duplicated root detection: rejects workspace/workspace/...
            - Optionally creates parent directories

        Raises PathContainmentError on violation.
        """
        raw = str(user_path).strip()

        # 1. Detect and reject double-root duplicates
        ws_name = self.workspace_root.name.lower()
        normalised_raw = raw.replace("\\", "/").lower()
        # If path starts with the workspace folder name twice
        if normalised_raw.startswith(f"{ws_name}/{ws_name}"):
            raise PathContainmentError(
                f"Duplicated workspace root in path '{raw}'. "
                f"Do not prefix paths with '{ws_name}/' when they are already relative "
                f"to the workspace root."
            )

        # 2. Resolve to absolute path
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        candidate = candidate.resolve()

        # 3. Containment check
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError:
            # Also allow paths relative to project_root (for tools operating on source)
            try:
                candidate.relative_to(self.project_root)
            except ValueError:
                raise PathContainmentError(
                    f"Path '{candidate}' is outside the allowed workspace root '{self.workspace_root}'. "
                    f"Tools must not access paths outside the workspace."
                )

        # 4. Optionally create parent directory
        if create_parents and not candidate.parent.exists():
            candidate.parent.mkdir(parents=True, exist_ok=True)

        return candidate

    def safe_path(self, *parts: str) -> Path:
        """Join parts under workspace_root and resolve safely."""
        return self.resolve_workspace_path(Path(*parts))


_GLOBAL_WORKSPACE_MGR: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """Return the singleton WorkspaceManager."""
    global _GLOBAL_WORKSPACE_MGR
    if _GLOBAL_WORKSPACE_MGR is None:
        _GLOBAL_WORKSPACE_MGR = WorkspaceManager.get_instance()
    return _GLOBAL_WORKSPACE_MGR
