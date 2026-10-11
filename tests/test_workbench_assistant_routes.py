"""Assistant HTTP boundaries: server-owned evidence and tenant ownership."""
import importlib
import hashlib
import uuid
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from fastapi import HTTPException

api = importlib.import_module("webapi.app")
A, B = str(uuid.uuid4()), str(uuid.uuid4())


@pytest.fixture
def local(tmp_path, monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "local")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.write_bytes(b"fixture-a")
    b.write_bytes(b"fixture-b")
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(api, "samples", {"test_a": a, "test_b": b})
    monkeypatch.setattr(api, "verified_hashes", {})
    monkeypatch.setattr(api, "results", {"result_a": {"id": "test_a", "result_id": "result_a", "model_sha": "active", "image_sha": hashlib.sha256(b"fixture-a").hexdigest()}})
    monkeypatch.setattr(api, "MODEL_SHA", "active")
    monkeypatch.setattr(api, "current_result", lambda sid: None)
    monkeypatch.setattr(api, "report", lambda: {"model_sha": "active", "checkpoint_matches_report": False, "metrics": None})
    return TestClient(api.app)


def test_http_context_comes_from_server_not_request(local, monkeypatch):
    captured = []
    def respond(question, context, use_provider, context_opt_in):
        captured.append(context)
        return {"answer": "fixture"}
    monkeypatch.setattr(api.assistant, "respond", respond)
    response = local.post("/api/assistant", json={"sample_id": "test_a", "result_id": "result_a", "question": "Summarise this result"})
    assert response.status_code == 200
    assert captured[0]["result"]["id"] == "test_a"
    assert captured[0]["report"]["metrics"] is None
    response = local.post("/api/assistant", json={"sample_id": "test_a", "question": "What is the accuracy?", "report": {"metrics": {"pixel_accuracy": 1}}})
    assert response.status_code == 422
    assert len(captured) == 1


@pytest.mark.parametrize("sample,result_id", [("test_b", "result_a"), ("test_a", "absent")])
def test_wrong_sample_or_result_does_not_reach_helper(local, monkeypatch, sample, result_id):
    monkeypatch.setattr(api.assistant, "respond", lambda *args: pytest.fail("must reject before assistant"))
    response = local.post("/api/assistant", json={"sample_id": sample, "result_id": result_id, "question": "Summarise this result"})
    assert response.status_code == 404


def test_stale_checkpoint_result_is_rejected(local, monkeypatch):
    api.results["result_a"]["model_sha"] = "old"
    response = local.post("/api/assistant", json={"sample_id": "test_a", "result_id": "result_a", "question": "Summarise this result"})
    assert response.status_code == 404


def test_changed_source_image_result_is_rejected(local):
    api.results["result_a"]["image_sha"] = "stale-source-sha"
    response = local.post("/api/assistant", json={"sample_id": "test_a", "result_id": "result_a", "question": "Summarise this result"})
    assert response.status_code == 404


def test_provider_consent_error_is_safe_http_response(local):
    response = local.post("/api/assistant", json={"sample_id": "test_a", "question": "Summarise this result", "use_provider": True})
    assert response.status_code == 403
    assert "Approve sharing" in response.json()["detail"]


def test_public_assistant_routes_require_auth_and_result_owner(local, tmp_path, monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "public")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_fixture")
    monkeypatch.setattr(api.cloud, "tenants", {})
    monkeypatch.setattr(api, "verified_hashes", {"test_a": "fixture"})
    def verify(token):
        if token not in (A, B): raise HTTPException(401, "Invalid session")
        return {"id": token, "token": token}
    monkeypatch.setattr(api.cloud, "verify", verify)
    assert local.get("/api/assistant/status").status_code == 401
    assert local.post("/api/assistant", json={"sample_id": "test_a", "question": "Summarise this result"}).status_code == 401
    context = api.cloud.identity.set({"id": A, "token": A})
    try:
        api.tenant()["results"]["result_a"] = {"id": "test_a", "result_id": "result_a", "model_sha": "active", "image_sha": hashlib.sha256(b"fixture-a").hexdigest()}
    finally:
        api.cloud.identity.reset(context)
    payload = {"sample_id": "test_a", "result_id": "result_a", "question": "Summarise this result"}
    assert local.post("/api/assistant", headers={"Authorization": "Bearer " + A}, json=payload).status_code == 200
    assert local.post("/api/assistant", headers={"Authorization": "Bearer " + B}, json=payload).status_code == 404
