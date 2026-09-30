"""Public boundary and tenant isolation tests without a privileged cloud key."""
import importlib
import uuid
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from fastapi import HTTPException
api = importlib.import_module("webapi.app")
cloud = api.cloud
A = str(uuid.uuid4())
B = str(uuid.uuid4())

@pytest.fixture
def public(tmp_path, monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "public")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_fixture")
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(cloud, "tenants", {})
    monkeypatch.setattr(cloud, "hydrate", lambda state: None)
    def verify(token):
        if token not in (A, B):
            raise HTTPException(401, "Invalid session")
        return {"id": token, "token": token}
    monkeypatch.setattr(cloud, "verify", verify)
    return TestClient(api.app)

@pytest.mark.parametrize("method,url,payload", [
    ("get", "/api/samples", None),
    ("get", "/api/jobs/private", None),
    ("post", "/api/inferences", {"sample_id":"test_11"}),
    ("post", "/api/upload", None),
    ("post", "/api/simulation-sessions", None),
    ("post", "/api/simulate", {"result_id":"private","session_id":"private"}),
    ("put", "/api/samples/test_11/record", {"expected_version":0,"record":{}}),
    ("get", "/api/samples/test_11/image", None),
])
def test_public_requires_bearer(public, method, url, payload):
    assert getattr(public, method)(url, json=payload).status_code == 401 if method != "get" else public.get(url).status_code == 401

def test_forged_session_denied(public):
    assert public.get("/api/samples", headers={"Authorization":"Bearer forged"}).status_code == 401

def test_public_configuration_and_health(public):
    assert public.get("/api/config").json()["auth_required"] is True
    assert public.get("/api/health").json()["cloud_sync"] is True

def test_private_jobs_results_samples_and_simulation_sessions(public, tmp_path):
    context = cloud.identity.set({"id":A,"token":A})
    try:
        state = api.tenant()
        state["jobs"]["private"] = {"id":"private","status":"queued"}
        state["results"]["private"] = {"id":"upload_private"}
        state["samples"]["upload_private"] = tmp_path / "private-image"
        a_store = api.workspace_store()
    finally:
        cloud.identity.reset(context)
    assert public.get("/api/jobs/private",headers={"Authorization":"Bearer "+A}).status_code == 200
    assert public.get("/api/jobs/private",headers={"Authorization":"Bearer "+B}).status_code == 404
    assert public.get("/api/samples/upload_private",headers={"Authorization":"Bearer "+B}).status_code == 404
    session = public.post("/api/simulation-sessions",headers={"Authorization":"Bearer "+A}).json()
    context = cloud.identity.set({"id":B,"token":B})
    try:
        assert api.workspace_store() != a_store
        assert "private" not in api.workspace_results()
        assert session["session_id"] not in api.workspace_sessions()
    finally:
        cloud.identity.reset(context)
    assert cloud.identity.get() is None

def test_public_without_cloud_fails_closed(monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT","public")
    monkeypatch.delenv("SUPABASE_URL",raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY",raising=False)
    assert TestClient(api.app).get("/api/samples").status_code == 503

def test_local_rejects_nonloopback(monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT","local")
    monkeypatch.delenv("SUPABASE_URL",raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY",raising=False)
    assert TestClient(api.app,client=("203.0.113.10",1234)).get("/api/samples").status_code == 403

def test_anonymous_user_rejected(monkeypatch):
    monkeypatch.setattr(cloud,"request",lambda *args,**kwargs: {"id":A,"is_anonymous":True})
    with pytest.raises(HTTPException) as exc:
        cloud.verify("token")
    assert exc.value.status_code == 403

def test_cloud_record_conflict_does_not_claim_success(monkeypatch):
    monkeypatch.setattr(cloud,"request",lambda *args,**kwargs: [])
    with pytest.raises(HTTPException) as exc:
        cloud.save_record("sample",3,{"notes":"stale"})
    assert exc.value.status_code == 409

def test_inference_worker_preserves_user_identity(public, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    monkeypatch.setattr(api,"samples",{"sample":tmp_path/"image"})
    monkeypatch.setattr(api,"verified_hashes",{"sample":"fixture"})
    monkeypatch.setattr(api,"MODEL_SHA","fixture")
    monkeypatch.setattr(cloud,"save_sample",lambda *args: None)
    observed = []
    def run(jid,sid,mode):
        observed.append(cloud.identity.get()["id"])
        api.workspace_jobs()[jid].update(status="complete")
    monkeypatch.setattr(api,"run_inference",run)
    with ThreadPoolExecutor(max_workers=1) as executor:
        monkeypatch.setattr(api,"pool",executor)
        response = public.post("/api/inferences",json={"sample_id":"sample"},headers={"Authorization":"Bearer "+A})
        assert response.status_code == 202
    assert observed == [A]
    jid=response.json()["id"]
    assert public.get("/api/jobs/"+jid,headers={"Authorization":"Bearer "+B}).status_code == 404

@pytest.mark.parametrize("key",["sb_secret_forbidden", "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.signature"])
def test_privileged_key_configuration_rejected(monkeypatch,key):
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY",key)
    with pytest.raises(RuntimeError):
        cloud.config()
