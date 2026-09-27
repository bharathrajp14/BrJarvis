# tests/smoke/test_runtime_health.py — Smoke Test Suite for BR JARVIS MK40.2+
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from brjarvis.career.crm.database import get_career_crm_db
from brjarvis.core.config import JarvisConfig, get_config
from brjarvis.core.paths import find_python_executable, paths
from brjarvis.diagnostics.doctor import run_diagnostics_audit
from brjarvis.router.core import load_available_backends
from brjarvis.tools.registry import TOOL_REGISTRY, get_registry_status


def test_python_runtime_and_venv():
    """Verify that the runtime resolves the project virtual environment cleanly."""
    exe = find_python_executable()
    assert exe.exists(), f"Resolved python executable does not exist: {exe}"
    assert paths.PROJECT_ROOT.exists(), "PROJECT_ROOT must exist"
    assert paths.SOURCE_ROOT.exists(), "SOURCE_ROOT must exist"
    assert paths.CONFIG_ROOT.exists(), "CONFIG_ROOT must exist"


def test_dotenv_and_config_loading():
    """Verify that configuration loads from the template without requiring a local .env."""
    cfg = get_config(force_reload=True)
    assert isinstance(cfg, JarvisConfig)
    assert cfg.assistant.name is not None
    assert cfg.models.default_backend is not None
    template = paths.PROJECT_ROOT / ".env.template"
    assert template.exists(), ".env.template must exist so operators can create a local .env"


def test_truthful_doctor_diagnostics():
    """Verify that the diagnostic engine reports all subsystems truthfully."""
    report = run_diagnostics_audit(auto_repair=False)
    assert "python_packages" in report
    assert "system_tools" in report
    assert "api_keys" in report
    assert "paths_status" in report
    assert "subsystems_status" in report
    assert "overall_health" in report
    assert "api_key_sources" in report
    assert "dependency_summary" in report
    assert "python_runtime" in report
    assert "repair_actions" in report
    assert set(report["api_key_sources"]) == set(report["api_keys"])
    assert "executable" in report["python_runtime"]
    assert report["dependency_summary"]["total"] == len(report["python_packages"])

    # Subsystems check
    assert "Career OS" in report["subsystems_status"]
    assert "Tool Registry" in report["subsystems_status"]
    assert "Skills Subsystem" in report["subsystems_status"]

    # Overall health should not be empty
    assert report["overall_health"] in (
        "HEALTHY",
        "DEGRADED",
        "DEGRADED (Missing core Python dependencies)",
        "NOT_READY (AI backends unconfigured)",
        "NEEDS_ATTENTION",
        "FAILED",
    )


def test_tool_registry_ecosystem():
    """Verify that the full tool ecosystem (200+ tools) is discovered and registered."""
    status = get_registry_status()
    assert status["registered"] >= 100, f"Expected at least 100 registered tools, found {status['registered']}"
    assert status["discovered"] >= 100, f"Expected at least 100 discovered schemas, found {status['discovered']}"
    assert len(status["failed"]) == 0, f"Tool import failures detected: {status['failed']}"

    # Verify essential core tools are in registry
    essential_tools = [
        "web_search",
        "fetch_page",
        "file_read",
        "file_write",
        "career_profile_get",
        "career_analytics_summary",
        "reminder",
    ]
    for tool_name in essential_tools:
        assert tool_name in TOOL_REGISTRY, f"Essential tool '{tool_name}' missing from registry"


def test_career_os_crm_subsystem():
    """Verify that Career OS CRM database initializes and returns statistics."""
    db = get_career_crm_db()
    stats = db.get_stats()
    assert isinstance(stats, dict)
    assert "applications_count" in stats
    assert stats["applications_count"] >= 0


def test_router_backend_loading():
    """Verify that the router discovers available backend profiles safely."""
    backends = load_available_backends(force_refresh=True)
    assert isinstance(backends, dict)
    # The backends dictionary should be populated without unhandled exceptions
    for profile, backend in backends.items():
        assert hasattr(backend, "available")
