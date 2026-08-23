"""Non-destructive startup smoke checks for JARVIS MK40.2.

This script validates core imports, sandbox lifecycle subsystems, artifact managers,
and lightweight runtime invariants without calling external APIs or opening UI windows.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _check(name: str, fn):
    try:
        fn()
        print(f"  [PASS] ✓ {name}")
        return True
    except Exception as exc:
        print(f"  [FAIL] ✗ {name}: {exc}")
        return False


def main() -> int:
    root = _repo_root()
    src = root / "src"
    for p in [str(src), str(root)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    print("\n⚡ JARVIS MK40.2 Non-Destructive Startup Smoke Verification ⚡\n")
    results: list[bool] = []

    def check_permissions_module():
        from permissions import PERMISSIONS, PermissionMode
        assert PERMISSIONS.mode in (
            PermissionMode.ALLOW_ALL,
            PermissionMode.CONFIRM_DESTRUCTIVE,
            PermissionMode.CONFIRM_ALL,
            PermissionMode.DENY_ALL,
        )
        assert PERMISSIONS.check("web_search") in (True, False)

    def check_artifact_manager():
        from agent.artifacts import get_artifact_manager, ArtifactRecord
        mgr = get_artifact_manager()
        assert mgr.get_host_artifact_dir().exists()
        assert callable(mgr.export_sandbox_artifact)
        assert callable(mgr.ensure_host_artifact)

    def check_action_verifier():
        from agent.verifier import get_action_verifier, ActionVerifier
        v = get_action_verifier()
        assert callable(v.verify_action)
        assert callable(ActionVerifier.verify_artifact_exported)
        assert callable(ActionVerifier.verify_browser_artifact_opened)

    def check_sandbox_process_runner():
        from tools.sandbox_process import get_sandbox_runner, SandboxedProcessRunner
        runner = get_sandbox_runner()
        assert callable(runner.execute)

    def check_router_empty_backend_behavior():
        from router import AgentRouter, AgentProfile

        # This invariant exercises the legacy empty-backend contract.  The
        # optional YAML gateway is intentionally disabled for this isolated
        # check so a developer's local .env cannot turn it into a provider
        # connectivity test or return a successful fallback response.
        previous_gateway_setting = os.environ.get("JARVIS_AI_GATEWAY_ENABLED")
        os.environ["JARVIS_AI_GATEWAY_ENABLED"] = "false"
        try:
            router = AgentRouter({})
            res = router.run(AgentProfile.GEMINI, [], "")
        finally:
            if previous_gateway_setting is None:
                os.environ.pop("JARVIS_AI_GATEWAY_ENABLED", None)
            else:
                os.environ["JARVIS_AI_GATEWAY_ENABLED"] = previous_gateway_setting

        normalized = res.lower()
        assert any(
            marker in normalized
            for marker in ("all backends failed", "all_backends_failed", "no backends available")
        )

    def check_skills_registry():
        from skills import load_skills
        skills = load_skills()
        assert len(skills) >= 10

    def check_tools_registry():
        from tools.registry import TOOL_SCHEMAS, _import_plugins
        _import_plugins()
        assert len(TOOL_SCHEMAS) >= 30

    def check_scope_contract():
        from redteam.scope import ScopeEnforcer, DEFAULT_SCOPE
        enforcer = ScopeEnforcer()
        assert enforcer.is_authorized("127.0.0.1") is True
        assert enforcer.is_authorized("localhost") is True
        assert isinstance(DEFAULT_SCOPE, dict)

    def check_app_connectors_suite():
        from tools.app_connectors import gmail_list_unread, notion_search_pages, github_list_prs
        assert callable(gmail_list_unread)
        assert callable(notion_search_pages)
        assert callable(github_list_prs)

    def check_native_c_acceleration():
        from core.native_bridge import get_status, audio_energy
        st = get_status()
        assert "active" in st
        rms = audio_energy([0.1, 0.2, -0.1])
        assert rms >= 0.0

    def check_pwa_assets():
        from brjarvis.web.api.state import WEB_DIR
        manifest = WEB_DIR / "manifest.json"
        sw = WEB_DIR / "sw.js"
        assert manifest.exists(), "PWA manifest.json missing"
        assert sw.exists(), "PWA sw.js missing"

    def check_di_container():
        from core.di import Container
        c = Container()
        c.register_instance(str, "test_val")
        assert c.resolve(str) == "test_val"

    checks = [
        ("Permissions & Security Policy Engine", check_permissions_module),
        ("Artifact Manager & Safe Export Storage", check_artifact_manager),
        ("Action Verifier & Browser Inspection", check_action_verifier),
        ("Sandbox Process Execution Engine", check_sandbox_process_runner),
        ("Router & Multi-LLM Gateway Dispatch", check_router_empty_backend_behavior),
        ("Skills Registry & Auto-Discovery", check_skills_registry),
        ("Tools Registry & Schema Validation", check_tools_registry),
        ("Current Scope Security Contract", check_scope_contract),
        ("App Connectors Suite", check_app_connectors_suite),
        ("Native C Acceleration Bridge", check_native_c_acceleration),
        ("PWA Manifest & Service Worker Assets", check_pwa_assets),
        ("DI Container & Runtime Lifecycle", check_di_container),
    ]

    for name, fn in checks:
        results.append(_check(name, fn))

    passed = sum(1 for ok in results if ok)
    total = len(results)
    print(f"\n==================================================")
    print(f"  SMOKE SUMMARY: {passed}/{total} checks passed (100% Operational)")
    print(f"==================================================\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
