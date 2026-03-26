from fastapi.testclient import TestClient


def test_healthcheck_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "app" in payload
    assert "env" in payload


def test_readiness_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready"}


def test_metrics_endpoint_is_exposed(client: TestClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "starter_api_http_requests_total" in response.text
