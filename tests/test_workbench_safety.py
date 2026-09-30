from webapi.app import refusal,MODEL_SHA
import time

def result(**changes):
    r={"verified":True,"model_sha":MODEL_SHA,"mode":"field","confidence":.95,
       "created_at":time.time(),"advisory":{"action":"Grind finer"}}
    r.update(changes)
    return r

def test_unknown_upload_never_commands_even_when_confident():
    assert "Unverified" in refusal(result(verified=False))

def test_low_confidence_is_held():
    assert "Confidence" in refusal(result(confidence=.84))

def test_full_section_is_advisory():
    assert "Full-section" in refusal(result(mode="full"))

def test_stale_is_held():
    assert "older" in refusal(result(created_at=time.time()-1801))

def test_continue_preserves_current_state():
    assert "retained" in refusal(result(advisory={"action":"Continue at current setpoint"}))

def test_valid_fresh_grind_advice_reaches_transport():
    assert refusal(result()) is None


def test_decision_export_requires_exact_event_and_result(tmp_path, monkeypatch):
    import importlib, json
    from fastapi import HTTPException
    import pytest
    api = importlib.import_module("webapi.app")
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(api, "results", {"r-one": {"id": "sample-one", "model_sha": "test-checkpoint"}})
    (tmp_path / "simulation-events.jsonl").write_text(json.dumps({"result_id":"r-other","created_at":1.0})+"\n"+json.dumps({"result_id":"r-one","created_at":2.0,"state":"held"})+"\n")
    with pytest.raises(HTTPException):
        api.decision_download("r-one", 1.0)
    with pytest.raises(HTTPException):
        api.decision_download("r-unknown", 2.0)
    response = api.decision_download("r-one", 2.0)
    payload = json.loads(response.body)
    assert payload["sample_id"] == "sample-one"
    assert payload["simulation"]["result_id"] == "r-one"
    assert payload["model_sha"] == "test-checkpoint"
    assert "attachment" in response.headers["content-disposition"]
