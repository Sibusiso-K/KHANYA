import pytest
pytest.importorskip("fastapi")
from webapi.app import refusal,MODEL_SHA
import time

def result(**changes):
    r={"verified":True,"verified_sample":"test_01","model_sha":MODEL_SHA,"mode":"field","confidence":.95,
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


def test_unverified_sample_refuses_even_if_legacy_verified_flag_is_true():
    assert "byte-for-byte" in refusal(result(verified_sample=None))

def test_copied_speed_advisor_confidence_gate_withholds_positive_action():
    from src import advisor
    recommendation = advisor.Recommendation("Grind finer", "Measured reason", "low - verify manually")
    held = advisor.confidence_gate(recommendation, .84)
    assert held.action == advisor.LOW_CONFIDENCE_ACTION
    assert "provisional" in held.reason
    abstention = advisor.Recommendation("Flag for manual review", "Already abstaining", "low")
    assert advisor.confidence_gate(abstention, .2) is abstention

def test_input_colour_checks_refuse_greyscale_and_cool_cast():
    from src.input_checks import colour_cast_reason
    from PIL import Image
    assert "no colour" in colour_cast_reason(Image.new("RGB", (8, 8), (90, 90, 90)))
    assert "colour balance" in colour_cast_reason(Image.new("RGB", (8, 8), (60, 100, 160)))

def test_test_11_original_bytes_match_the_committed_manifest():
    from src.input_checks import validated_sample
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "data/raw/lumenstone/S2_v2/imgs/test/test_11.jpg"
    if not path.is_file():
        import pytest
        pytest.skip("held-out image data is not installed in this checkout")
    assert validated_sample(path.read_bytes()) == "test_11"


def test_verified_sample_matches_exact_raw_bytes(monkeypatch):
    import hashlib
    from src import input_checks as inputs
    sample = b"held-out sample bytes"
    monkeypatch.setattr(inputs, "_VALIDATED", {hashlib.sha256(sample).hexdigest(): "test_11"})
    assert inputs.validated_sample(sample) == "test_11"
    assert inputs.validated_sample(sample + b"changed") is None

def test_upload_endpoint_refuses_greyscale_before_storing(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from webapi import app as api
    from io import BytesIO
    from PIL import Image
    upload_dir = tmp_path / "uploads"; upload_dir.mkdir()
    monkeypatch.setattr(api, "UPLOADS", upload_dir)
    monkeypatch.setattr(api, "samples", {})
    stream = BytesIO(); Image.new("RGB", (512, 512), (90, 90, 90)).save(stream, format="JPEG")
    response = TestClient(api.app).post("/api/upload", files={"file": ("grey.jpg", stream.getvalue(), "image/jpeg")})
    assert response.status_code == 400
    assert "no colour" in response.json()["detail"]
    assert not list(upload_dir.iterdir())


def test_corrupt_upload_uses_plain_actionable_message_not_buffer_repr(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from webapi import app as api
    upload_dir = tmp_path / "uploads"; upload_dir.mkdir()
    monkeypatch.setattr(api, "UPLOADS", upload_dir)
    monkeypatch.setattr(api, "samples", {})
    response = TestClient(api.app).post("/api/upload", files={"file": ("broken.jpg", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "This file could not be read as an image. Choose an intact JPG, PNG or TIFF micrograph."
    assert "BytesIO" not in response.text
    assert not list(upload_dir.iterdir())

