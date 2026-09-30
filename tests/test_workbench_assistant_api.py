"""Authenticated assistant context is resolved by the server, never the browser."""
import importlib
import uuid
import hashlib
from pathlib import Path
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
api=importlib.import_module("webapi.app")

@pytest.fixture
def local(monkeypatch,tmp_path):
    source=tmp_path/"sample.jpg"
    source.write_bytes(b"source")
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "local")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.setattr(api, "sample_path", lambda sid: source if sid == "sample" else (_ for _ in ()).throw(api.HTTPException(404, "Sample not found")))
    monkeypatch.setattr(api, "results", {"current":{"id":"sample","result_id":"current","model_sha":api.MODEL_SHA,"image_sha":hashlib.sha256(b"source").hexdigest(),"phases":[],"confidence":.6}})
    monkeypatch.setattr(api, "current_result", lambda sid: None)
    return TestClient(api.app)

def test_server_resolves_result_and_ignores_forged_context(local):
    response=local.post("/api/assistant",json={"sample_id":"sample","result_id":"current","question":"What model is used?"})
    assert response.status_code==200
    assert "DeepLabV3 / ResNet-50" in response.json()["answer"]
    assert local.post("/api/assistant",json={"sample_id":"sample","question":"accuracy","context":{"accuracy":1}}).status_code==422

def test_result_cannot_cross_sample_or_checkpoint(local,monkeypatch):
    for result in ({"id":"other","model_sha":api.MODEL_SHA},{"id":"sample","model_sha":"stale"}):
        monkeypatch.setattr(api,"results",{"current":result})
        assert local.post("/api/assistant",json={"sample_id":"sample","result_id":"current","question":"phases"}).status_code==404

def test_provider_requires_explicit_opt_in_and_status_has_no_secret(local,monkeypatch):
    monkeypatch.setenv("REEFPRINT_ASSISTANT_API_KEY","test-secret")
    assert "test-secret" not in local.get("/api/assistant/status").text
    assert local.post("/api/assistant",json={"sample_id":"sample","question":"phases","use_provider":True}).status_code==403

def test_assistant_requires_auth_on_public(local,monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT","public")
    monkeypatch.setenv("SUPABASE_URL","https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY","sb_publishable_test")
    assert local.get("/api/assistant/status").status_code==401
    assert local.post("/api/assistant",json={"sample_id":"sample","question":"phases"}).status_code==401
