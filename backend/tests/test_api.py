"""
AUDITRA API & Health Contract Tests
Owner: Amulya Dongre

Validates Section 12 API Endpoints:
1. GET /api/health returns 200 OK and valid health payload.
2. GET /api/scenarios returns available synthetic scenarios.
3. POST /api/replay rejects naive timestamps with 422 Unprocessable Entity.
4. POST /api/replay with valid timezone-aware payload parses cleanly into ReplayRequest.
"""

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_healthy():
    """Verify health check endpoint returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AUDITRA-Backend"
    assert "version" in data
    assert "timestamp" in data


def test_list_scenarios_returns_synthetic_scenarios():
    """Verify scenarios endpoint lists scenarios with required metadata."""
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 3
    scenario_ids = [s["scenario_id"] for s in scenarios]
    assert "SCENARIO-01-THERMAL-TRIP" in scenario_ids
    assert "SCENARIO-02-GRID-CURTAILMENT-WEATHER" in scenario_ids
    assert "SCENARIO-03-SENSOR-DRIFT" in scenario_ids


def test_replay_endpoint_rejects_naive_timestamp():
    """Verify replay endpoint rejects timestamps without timezone information."""
    payload = {
        "scenario_id": "SCENARIO-01-THERMAL-TRIP",
        "replay_time": "2026-06-15T12:00:00"  # Missing timezone offset!
    }
    response = client.post("/api/replay", json=payload)
    assert response.status_code == 422


def test_replay_endpoint_accepts_valid_utc_timestamp():
    """Verify replay endpoint accepts valid ISO-8601 UTC timestamp."""
    payload = {
        "scenario_id": "SCENARIO-01-THERMAL-TRIP",
        "replay_time": "2026-06-15T12:00:00Z"
    }
    response = client.post("/api/replay", json=payload)
    # 501 indicates the Pydantic schema passed validation and reached the stub boundary
    assert response.status_code == 501
    assert "Phase 2" in response.json()["detail"]
