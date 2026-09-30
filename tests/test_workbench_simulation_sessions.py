import importlib
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

api = importlib.import_module("webapi.app")


@pytest.fixture
def session_api(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(api, "plants", {})
    monkeypatch.setattr(api, "plant_sessions", set())
    monkeypatch.setattr(api, "results", {"r": {"result_id": "r", "verified": False}})
    return TestClient(api.app)


def test_api_issued_simulator_sessions_keep_independent_state(session_api):
    first = session_api.post("/api/simulation-sessions", json={}).json()["session_id"]
    second = session_api.post("/api/simulation-sessions", json={}).json()["session_id"]
    assert first != second
    event_a = session_api.post("/api/simulate", json={"result_id": "r", "session_id": first}).json()
    event_b = session_api.post("/api/simulate", json={"result_id": "r", "session_id": second}).json()
    assert event_a["state"] == event_b["state"] == "held"
    assert event_a["before"] == event_a["after"] == 0
    assert event_b["before"] == event_b["after"] == 0
    assert session_api.post("/api/simulate", json={"result_id": "r", "session_id": "invented"}).status_code == 404
