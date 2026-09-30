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

