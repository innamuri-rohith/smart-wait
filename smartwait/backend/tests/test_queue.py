"""Tests for queue, services, counters, and calling engine."""
from tests.helpers import make_user
from app.db.models import Role


def test_services_list(client):
    r = client.get("/api/queue/services")
    assert r.status_code == 200
    services = r.json()
    assert len(services) >= 3
    names = [s["name"] for s in services]
    assert "Banking Services" in names
    assert "Healthcare Services" in names
    assert "Customer Support" in names


def test_counters_list(client):
    r = client.get("/api/queue/counters")
    assert r.status_code == 200
    counters = r.json()
    assert len(counters) >= 3


def test_join_queue_and_status(client):
    payload = {
        "service_id": 1,
        "customer_name": "Arjun Kumar",
        "customer_email": "arjun@example.com",
        "priority_category": "general"
    }
    r = client.post("/api/queue/join", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["token_code"].startswith("A-")
    assert data["service_name"] == "Banking Services"
    assert data["status"] == "waiting"

    # Status check
    r_status = client.get(f"/api/queue/status/{data['token_code']}")
    assert r_status.status_code == 200
    assert r_status.json()["token_code"] == data["token_code"]


def test_call_next_token(client):
    # Join queue
    client.post("/api/queue/join", json={
        "service_id": 1,
        "customer_name": "Test Customer",
        "priority_category": "general"
    })

    # Call next
    r = client.post("/api/queue/call-next", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "called"
    assert data["counter_code"] is not None


def test_analytics(client):
    r = client.get("/api/queue/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "total_tokens_today" in data
    assert "hourly_stats" in data
    assert len(data["hourly_stats"]) == 4

