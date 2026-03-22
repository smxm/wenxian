from __future__ import annotations

from fastapi.testclient import TestClient

from literature_screening.api.app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta_endpoint() -> None:
    response = client.get("/api/meta")
    assert response.status_code == 200
    payload = response.json()
    assert {item["provider"] for item in payload["providers"]} == {"deepseek", "kimi"}
    assert ".ris" in payload["acceptedInputFormats"]


def test_project_create_and_list() -> None:
    created = client.post(
        "/api/projects",
        json={"name": "api-test-project", "topic": "api topic", "description": "desc"},
    )
    assert created.status_code == 200
    project = created.json()
    assert project["name"] == "api-test-project"

    listing = client.get("/api/projects")
    assert listing.status_code == 200
    assert any(item["id"] == project["id"] for item in listing.json())
