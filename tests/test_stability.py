import numpy as np
from PIL import Image

from dashboard.control import command_for
from src import advisor, stability
from src.advisor import Recommendation


def _rec(action):
    return Recommendation(action, "reason", "high")


def test_shift_is_the_measured_v1_median_and_darkens_every_channel():
    assert stability.REIMAGING_SHIFT_RGB == (-34.8, -32.5, -29.6)
    out = np.asarray(stability.reimaged(Image.new("RGB", (4, 4), (100, 100, 100))))
    assert tuple(out[0, 0]) == (65, 67, 70)   # truncated toward zero on uint8 cast


def test_shift_clips_rather_than_wraps():
    out = np.asarray(stability.reimaged(Image.new("RGB", (2, 2), (10, 10, 10))))
    assert out.min() == 0


def test_same_advice_after_the_shift_is_kept():
    kept = stability.gate(_rec("Grind finer"), "Grind finer")
    assert kept.action == "Grind finer"


def test_changed_confident_advice_is_refused_and_the_plant_holds():
    refused = stability.gate(_rec("Grind finer"), "Marginal - verify before acting")
    assert refused.action == stability.UNSTABLE_ACTION
    assert "Grind finer" in refused.reason and "Marginal" in refused.reason
    assert advisor.verdict_state(refused.action)[0] == "hold"
    assert command_for(refused.action)[0] is None


def test_an_abstention_is_left_alone_whatever_the_shift_says():
    for action in ("Marginal - verify before acting", "No recommendation - too few payload particles"):
        assert stability.gate(_rec(action), "Grind finer").action == action
