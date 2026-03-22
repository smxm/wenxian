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
