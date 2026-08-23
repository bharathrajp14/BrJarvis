"""Integration tests for FastAPI REST Endpoints via TestClient."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from brjarvis.web.api.server import create_app
from brjarvis.web.api.state import SERVER_API_KEY, WEB_DIR


@pytest.mark.integration
def test_fastapi_health_endpoint():
    """Verify GET /health returns 200 OK."""
    app = create_app()
    client = TestClient(app)

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data or "ok" in str(data).lower()


@pytest.mark.integration
def test_fastapi_connectors_endpoint():
    """Verify GET /api/connectors returns available integrations."""
    app = create_app()
    client = TestClient(app)

    unauthorized = client.get("/api/connectors")
    assert unauthorized.status_code == 401

    resp = client.get("/api/connectors", headers={"X-API-Key": SERVER_API_KEY})
    assert resp.status_code == 200
    assert isinstance(resp.json(), (list, dict))


@pytest.mark.integration
def test_fastapi_login_creates_authenticated_cookie_session():
    """The API key is exchanged for an HttpOnly session instead of bypassing auth locally."""
    client = TestClient(create_app())

    invalid = client.post("/api/auth/login", json={"api_key": "invalid-key"})
    assert invalid.status_code == 401

    valid = client.post("/api/auth/login", json={"api_key": SERVER_API_KEY})
    assert valid.status_code == 200

    assert "jarvis_session" in valid.cookies
    assert "session_token" not in valid.json()

    authenticated = client.get("/api/connectors")

    assert authenticated.status_code == 200


@pytest.mark.integration
def test_dashboard_career_routes_match_openapi_contract():
    app = create_app()
    paths = app.openapi()["paths"]

    assert "get" in paths["/api/career/jobs/search"]
    assert "post" in paths["/api/career/resumes/create"]
    assert "post" in paths["/api/career/ats/score"]
    assert "post" in paths["/api/career/spreadsheet/sync"]

    dashboard_js = (WEB_DIR / "app.js").read_text(encoding="utf-8")
    assert "/api/career/jobs/search?query=" in dashboard_js
    assert "/api/career/resumes/create" in dashboard_js
    assert "/api/career/ats/score" in dashboard_js
    assert "/api/career/resume/generate" not in dashboard_js
    assert "/api/career/resume/ats-audit" not in dashboard_js


@pytest.mark.integration
def test_versioned_contacts_contract_and_path_containment(monkeypatch, tmp_path):
    from brjarvis.memory.contact_manager import UnifiedContactStore

    store = UnifiedContactStore(storage_path=tmp_path / "contacts.enc", legacy_path=tmp_path / "contacts.json")
    monkeypatch.setattr("brjarvis.memory.contact_manager.get_contact_store", lambda: store)
    client = TestClient(create_app())
    headers = {"X-API-Key": SERVER_API_KEY}

    created = client.post("/api/v1/contacts", json={"name": "Ada Lovelace", "email": "ada@example.test"}, headers=headers)
    assert created.status_code == 200
    assert created.json()["contact"]["name"] == "Ada Lovelace"

    listed = client.get("/api/v1/contacts?query=ada", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    contact_id = created.json()["contact"]["id"]
    updated = client.patch(f"/api/v1/contacts/{contact_id}", json={"phone_number": "+1 (555) 123-4567", "is_important": True}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["contact"]["phone_number"] == "+15551234567"
    assert updated.json()["contact"]["is_important"] is True

    deleted = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/v1/contacts?query=ada", headers=headers).json()["total"] == 0

    outside = client.post(
        "/api/v1/import/contacts",
        data={"file_path": str(tmp_path.parent / "outside.vcf")},
        headers=headers,
    )
    assert outside.status_code == 400


@pytest.mark.integration
def test_connector_config_uses_vault_and_metadata_only(monkeypatch, tmp_path):
    from brjarvis.security.credentials import CredentialVault
    from brjarvis.web.api.routes import connectors as connector_routes

    class MemoryBackend:
        def __init__(self):
            self.values = {}

        def set_password(self, service_name, username, password):
            self.values[(service_name, username)] = password

        def get_password(self, service_name, username):
            return self.values.get((service_name, username))

        def delete_password(self, service_name, username):
            self.values.pop((service_name, username), None)

    backend = MemoryBackend()
    vault = CredentialVault(vault_path=tmp_path / "credential_vault.json", backend=backend, service_name="test")
    monkeypatch.setattr(connector_routes, "_SETTINGS_FILE", tmp_path / "connector_settings.json")
    monkeypatch.setattr("brjarvis.security.credentials.get_credential_vault", lambda: vault)

    client = TestClient(create_app())
    response = client.post(
        "/api/v1/connector/config",
        json={"connector": "github", "api_key": "connector-secret", "settings": {"workspace": "demo"}},
        headers={"X-API-Key": SERVER_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["credential_ref"] == "connector:github:api_key"
    settings_text = (tmp_path / "connector_settings.json").read_text(encoding="utf-8")
    assert "connector-secret" not in settings_text
    assert vault.get_credential("connector:github:api_key") == "connector-secret"


@pytest.mark.integration
def test_project_upload_sanitizes_client_filename(monkeypatch, tmp_path):
    from brjarvis.web.api.routes import projects as project_routes

    class Project:
        def to_dict(self):
            return {"project_id": "project-1", "name": "Test"}

    class FileRecord:
        def to_dict(self):
            return {"filename": "payload.txt"}

    class Store:
        def get_project(self, project_id):
            return Project() if project_id == "project-1" else None

        def add_project_file(self, **kwargs):
            assert kwargs["filename"] == "payload.txt"
            assert ".." not in kwargs["file_path"]
            return FileRecord()

    monkeypatch.setattr(project_routes, "get_workspace_store", lambda: Store())
    monkeypatch.setattr(project_routes.paths, "ARTIFACT_ROOT", tmp_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/projects/project-1/files",
        files={"file": ("../../payload.txt", b"safe content", "text/plain")},
        headers={"X-API-Key": SERVER_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["file"]["filename"] == "payload.txt"


@pytest.mark.integration
def test_memory_delete_reports_missing_records(monkeypatch):
    from brjarvis.memory import persistent_store

    monkeypatch.setattr(persistent_store, "delete_memory", lambda name, scope="user": False)
    client = TestClient(create_app())
    response = client.delete("/api/v1/memory/missing", headers={"X-API-Key": SERVER_API_KEY})
    assert response.status_code == 404


@pytest.mark.integration
def test_career_profile_is_available_under_both_api_versions():
    client = TestClient(create_app())
    headers = {"X-API-Key": SERVER_API_KEY}
    legacy = client.get("/api/career/profile", headers=headers)
    versioned = client.get("/api/v1/career/profile", headers=headers)
    assert legacy.status_code == 200
    assert versioned.status_code == 200
    assert "profile" in legacy.json()
    assert "profile" in versioned.json()


@pytest.mark.integration
def test_normalized_routers_do_not_create_doubled_versioned_paths():
    paths = create_app().openapi()["paths"]
    assert not any(path.startswith("/api/v1/api/") for path in paths)
    for path in ("/api/v1/auth/status", "/api/v1/notifications", "/api/v1/conversations", "/api/v1/tasks", "/api/v1/agent/tasks", "/api/v1/projects", "/api/v1/artifacts", "/api/v1/contacts", "/api/v1/connectors", "/api/v1/career/profile"):
        assert path in paths
