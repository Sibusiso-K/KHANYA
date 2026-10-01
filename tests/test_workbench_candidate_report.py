"""Candidate evidence must not be confused with active-model metrics or approval."""
import json
from pathlib import Path
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from webapi import app as api, candidate_report

@pytest.fixture
def local(monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "local")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    return TestClient(api.app)

def test_verified_candidate_is_separate_from_active_metrics_and_approval(local, monkeypatch):
    live_sha = api.KNOWN_SHA
    monkeypatch.setattr(api, "MODEL_SHA", live_sha)
    prior = local.get("/api/report").json()
    response = local.get("/api/reports/native-candidate")
    assert response.status_code == 200
    evidence = response.json()
    assert evidence["verified_evidence"]
    assert evidence["model_sha"] == candidate_report.CHECKPOINT_SHA != live_sha
    assert evidence["deployment_status"] == "candidate-not-deployed"
    assert evidence["candidate_is_active"] is False
    assert evidence["protocol_sha"] == candidate_report.PROTOCOL_SHA
    assert evidence["metrics"]["n_test_sections"] == 12
    assert evidence["metrics"]["mean_iou"] == pytest.approx(.6320380215266846)
    magnetite = next(row for row in evidence["metrics"]["classes"] if row["name"] == "magnetite")
    assert magnetite["false_positive_pixels"] == 2140808
    assert magnetite["precision"] == pytest.approx(.2552887588957666)
    assert any("not a controlled uplift" in warning for warning in evidence["limitations"])
    assert local.get("/api/report").json() == prior
    assert api.APPROVED_MODEL_SHA != candidate_report.CHECKPOINT_SHA

def test_future_active_candidate_cannot_be_labelled_not_deployed(local, monkeypatch):
    monkeypatch.setattr(api, "MODEL_SHA", candidate_report.CHECKPOINT_SHA)
    evidence = local.get("/api/reports/native-candidate").json()
    assert evidence["candidate_is_active"] is True
    assert evidence["deployment_status"] == "active-checkpoint"
    assert local.get("/api/health").json()["model_approved"] is False

@pytest.mark.parametrize("key", list(candidate_report.ARTIFACTS))
def test_fixed_download_matches_recorded_hash(local, key):
    import hashlib
    response = local.get("/api/reports/native-candidate/download/" + key)
    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == candidate_report.ARTIFACTS[key][1]
    assert 'attachment' in response.headers['content-disposition']
    assert response.headers['cache-control'] == 'private, no-store'

def test_public_candidate_report_and_download_require_auth(local, monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "public")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
    for route in ("/api/reports/native-candidate", "/api/reports/native-candidate/download/metrics"):
        assert local.get(route).status_code == 401

def test_unknown_artifact_cannot_supply_filesystem_path(local):
    assert local.get("/api/reports/native-candidate/download/checkpoints").status_code == 404

def test_tampered_metrics_are_not_served(local, monkeypatch, tmp_path):
    for key in ("metrics", "protocol"):
        path, _ = candidate_report.verified_artifact(api.CANDIDATE_EVIDENCE_DIR, key)
        (tmp_path / path.name).write_bytes(path.read_bytes())
    path = tmp_path / candidate_report.ARTIFACTS["metrics"][0]
    measured = json.loads(path.read_text())
    measured["mean_iou"] = 1
    path.write_text(json.dumps(measured))
    monkeypatch.setattr(api, "CANDIDATE_EVIDENCE_DIR", tmp_path)
    assert local.get("/api/reports/native-candidate").status_code == 503
    assert local.get("/api/reports/native-candidate/download/metrics").status_code == 503
