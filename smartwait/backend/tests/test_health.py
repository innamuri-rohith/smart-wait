"""Smoke test: the application starts and the health endpoint responds."""


def test_health_endpoint(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
