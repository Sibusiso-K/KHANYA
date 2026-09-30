"""The confidence gate (pre-production finding 3)."""
from src.advisor import (ABSTAINING_PREFIXES, CONFIDENCE_FLOOR, LOW_CONFIDENCE_ACTION,
                         Recommendation, confidence_gate, verdict_state)


def _rec(action):
    return Recommendation(action, "reason", "high")


def test_confident_action_below_the_floor_is_withheld():
    gated = confidence_gate(_rec("Continue at current setpoint"), 0.64)
    assert gated.action == LOW_CONFIDENCE_ACTION
    assert gated.action.startswith(ABSTAINING_PREFIXES)
    assert "64%" in gated.reason and "Continue at current setpoint" in gated.reason
    assert "provisional" in gated.reason
    assert verdict_state(gated.action)[0] == "hold"


def test_confident_action_at_or_above_the_floor_passes():
    rec = _rec("Grind finer")
    assert confidence_gate(rec, CONFIDENCE_FLOOR) is rec
    assert confidence_gate(rec, 0.91) is rec


def test_abstentions_pass_through_whatever_the_confidence():
    rec = _rec("Marginal - verify before acting (grind finer or continue)")
    assert confidence_gate(rec, 0.1) is rec


def test_floor_matches_the_committed_evidence():
    import json
    from src.segmentation import config

    rows = json.loads((config.ROOT / "reports" / "confidence_calibration_trainval.json").read_text())["rows"]
    assert all(r["split"] in ("train", "validation") for r in rows)  # no test section
    unsafe = [r["confidence"] for r in rows if r["confident"] and r["severity"] == "unsafe"]
    correct = [r["confidence"] for r in rows if r["confident"] and r["severity"] == "agrees"]
    assert unsafe and max(unsafe) < CONFIDENCE_FLOOR  # every unsafe call is withheld
    assert sum(c >= CONFIDENCE_FLOOR for c in correct) == 3 and len(correct) == 5
