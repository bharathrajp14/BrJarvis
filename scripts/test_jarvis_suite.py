# scripts/test_jarvis_suite.py — BR JARVIS Automated Integration Test Suite
"""
Executes full end-to-end integration test matrix for BR JARVIS features:
1. 0-Token Intent Engine & Excel Analysis Exporter
2. Word (.docx) & PDF (.pdf) Document Generators
3. System Diagnostics & Process Telemetry
4. Codebase AST Compiler & Security Auditor
5. BR_WORKSPACE Self-Organizing Vault & Timeline Engine
6. Live OS Controller Initialization (Unlimited Mode)
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
for p in [str(BASE_DIR / "src" / "brjarvis"), str(BASE_DIR / "src"), str(BASE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def run_full_suite():
    logger.info("=" * 65)
    logger.info(" [TEST] BR JARVIS MK37 AUTOMATED INTEGRATION TEST SUITE")
    logger.info("=" * 65)

    results = []

    # 1. Test Excel Codebase Analysis (0-Token Intent)
    t0 = time.perf_counter()
    try:
        from core.intent_engine import DeterministicIntentEngine
        res1 = DeterministicIntentEngine.parse_and_execute("create the jarvis poject full analisis to that sheet")
        dt1 = (time.perf_counter() - t0) * 1000
        ok1 = res1 is not None and res1.get("executed", False)
        results.append(("0-Token Excel Analysis Exporter", ok1, f"{dt1:.2f}ms", res1.get("target") if ok1 else "Failed"))
    except Exception as e:
        results.append(("0-Token Excel Analysis Exporter", False, "0ms", str(e)))
    logger.info("  [1/6] Completed 0-Token Excel Analysis Exporter: %s", results[-1][1])

    # 2. Test Word & PDF Document Generator
    t0 = time.perf_counter()
    try:
        from tools.doc_tools import generate_project_product_analysis
        res2 = generate_project_product_analysis({"auto_open": False})
        dt2 = (time.perf_counter() - t0) * 1000
        ok2 = ("DOCX" in res2 or "Word" in res2) and "PDF" in res2
        results.append(("Word (.docx) & PDF (.pdf) Generator", ok2, f"{dt2:.2f}ms", "Generated .docx & .pdf"))
    except Exception as e:
        results.append(("Word (.docx) & PDF (.pdf) Generator", False, "0ms", str(e)))
    logger.info("  [2/6] Completed Word & PDF Generator: %s", results[-1][1])

    # 3. Test System Diagnostics & Telemetry
    t0 = time.perf_counter()
    try:
        from tools.process_tools import get_system_diagnostics
        res3 = get_system_diagnostics({})
        dt3 = (time.perf_counter() - t0) * 1000
        ok3 = "CPU Usage" in res3 or "RAM" in res3 or "Top Processes" in res3
        results.append(("System Diagnostics & Telemetry", ok3, f"{dt3:.2f}ms", "Captured CPU, RAM & Top 10 PIDs"))
    except Exception as e:
        results.append(("System Diagnostics & Telemetry", False, "0ms", str(e)))
    logger.info("  [3/6] Completed System Diagnostics: %s", results[-1][1])

    # 4. Test Codebase Security Auditor
    t0 = time.perf_counter()
    try:
        from tools.audit_tools import audit_codebase
        res4 = audit_codebase({})
        dt4 = (time.perf_counter() - t0) * 1000
        ok4 = "SECURITY & QUALITY AUDIT REPORT" in res4
        results.append(("AST Syntax & Security Auditor", ok4, f"{dt4:.2f}ms", "Scanned files for syntax & security"))
    except Exception as e:
        results.append(("AST Syntax & Security Auditor", False, "0ms", str(e)))
    logger.info("  [4/6] Completed AST Syntax & Security Auditor: %s", results[-1][1])

    # 5. Test BR_WORKSPACE & Timeline Engine
    t0 = time.perf_counter()
    try:
        from core.workspace_engine import CognitiveWorkspaceEngine
        ws = CognitiveWorkspaceEngine()
        ws.log_timeline_event("SUITE_TEST", "Executed automated integration test suite.")
        from tools.workspace_tools import get_workspace_timeline
        res5 = get_workspace_timeline({"limit": 5})
        dt5 = (time.perf_counter() - t0) * 1000
        ok5 = "BR_WORKSPACE TIMELINE" in res5
        results.append(("BR_WORKSPACE Vault & Timeline Stream", ok5, f"{dt5:.2f}ms", "SQLite event stream verified"))
    except Exception as e:
        results.append(("BR_WORKSPACE Vault & Timeline Stream", False, "0ms", str(e)))
    logger.info("  [5/6] Completed BR_WORKSPACE Vault & Timeline: %s", results[-1][1])

    # 6. Test Live OS Unlimited Mode Initialization
    t0 = time.perf_counter()
    try:
        from actions.live_os_control import LiveOSController
        ctrl = LiveOSController("test goal", max_steps=0)
        dt6 = (time.perf_counter() - t0) * 1000
        ok6 = ctrl.max_steps == 999999
        results.append(("Live OS Control (0=Unlimited Mode)", ok6, f"{dt6:.2f}ms", f"max_steps={ctrl.max_steps}"))
    except Exception as e:
        results.append(("Live OS Control (0=Unlimited Mode)", False, "0ms", str(e)))
    logger.info("  [6/6] Completed Live OS Control: %s", results[-1][1])

    # Print Summary Table
    logger.info("\n" + "-" * 65)
    logger.info(f"{'Feature / Engine':<38} | {'Status':<8} | {'Latency':<9} | Details")
    logger.info("-" * 65)

    passed_count = 0
    for name, ok, lat, detail in results:
        status_str = "[PASS]" if ok else "[FAIL]"
        if ok:
            passed_count += 1
        logger.info(f"{name:<38} | {status_str:<8} | {lat:<9} | {detail}")

    logger.info("-" * 65)
    logger.info(f"RESULT: {passed_count}/{len(results)} Test Cases Passed Successfully.")
    logger.info("=" * 65 + "\n")

    # Generate Markdown Report Artifact
    report_lines = [
        "# 🧪 BR JARVIS MK37 Integration Test Report",
        "",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "**Environment:** Windows (Native C FNV-1a Bridge + Python 3.14)",
        f"**Test Result:** {passed_count}/{len(results)} Passed",
        "",
        "| Feature Engine | Status | Latency | Result Details |",
        "| :--- | :---: | :---: | :--- |"
    ]

    for name, ok, lat, detail in results:
        status_icon = "[PASS]" if ok else "[FAIL]"
        report_lines.append(f"| **{name}** | {status_icon} | `{lat}` | {detail} |")

    report_path = BASE_DIR / "workspace" / "self_test_report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    logger.info(f"Generated Test Report Artifact at: '{report_path}'")


if __name__ == "__main__":
    run_full_suite()
