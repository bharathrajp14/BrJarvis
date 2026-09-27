from __future__ import annotations

from fastapi.testclient import TestClient

from jarvis.core.bootstrap import run_doctor
from jarvis.surfaces.web.server import create_app as create_jarvis_app


def test_run_doctor_structure() -> None:
    report = run_doctor()
    assert isinstance(report, dict)
    assert "status" in report
    assert "runtime" in report
    assert "directories" in report
    assert "database" in report
    assert "tools" in report
    assert "browser" in report
    assert "packages" in report

    # Check directory probe results
    dirs = report["directories"]
    assert "workspace" in dirs
    assert dirs["workspace"]["exists"] is True

    # Check database report
    db = report["database"]
    assert db["status"] == "healthy"
    assert "tasks" in db["tables"]


def test_jarvis_health_and_diagnostics_endpoints() -> None:
    app = create_jarvis_app()
    client = TestClient(app)

    # 1. /health and /healthz
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_z = client.get("/healthz")
    assert res_z.status_code == 200

    # 2. /ready and /readyz
    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"

    # 3. /diagnostics
    res_diag = client.get("/diagnostics")
    assert res_diag.status_code == 200
    data = res_diag.json()
    assert "status" in data
    assert "directories" in data

    # 4. /metrics
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert metrics_data["status"] == "online"
    assert "timestamp" in metrics_data
