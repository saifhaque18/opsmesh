from fastapi.testclient import TestClient

from src.opsmesh.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "opsmesh-api"


def test_list_incidents_placeholder():
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert data["total"] == 0
