"""verdict_state() is tested elsewhere (test_verdict_state.py) only against
hand-typed literal strings, decoupled from advise() on purpose so its
prefix-matching logic can be tested without the full advisor. That decoupling
has a cost: nothing checks that advise()'s ACTUAL output strings still match
what verdict_state() expects. If a future edit renames or adds an action in
advisor.py without updating verdict_state()'s prefixes, every existing test
would still pass - test_verdict_state.py's literals wouldn't know, and
advise()'s own tests never call verdict_state() at all.

This file closes that gap: it drives every branch of advise() with real
inputs and checks the REAL resulting action string maps to the CORRECT
verdict_state() class - never the "unrecognised action" fallback, and never
green except for the one action that should be.
"""
import pytest

from src import advisor
from src.advisor import verdict_state
from src.modal import ModalResult


def _result(liberation=0.9, payload=0.05, ore_area=0.8, n_particles=12,
            payload_pixels=500, extra_roles=None):
    role_fractions = {"payload": payload, "gangue": 1.0 - payload}
    if extra_roles:
        role_fractions.update(extra_roles)
    return ModalResult(
        phase_fractions={"chalcopyrite": payload, "pyrite": 1.0 - payload},
        role_fractions=role_fractions,
        ore_area_fraction=ore_area,
        liberation=liberation,
        n_particles=n_particles,
        payload_pixels=payload_pixels,
    )


# Each entry drives advise() to one real branch, and states which
# verdict_state() class the resulting action must land in.
CASES = [
    ("invalid measurement", dict(kwargs={}, mean_confidence=1.5), "hold"),
    ("insufficient ore", dict(kwargs={"ore_area": 0.001}, mean_confidence=0.9), "hold"),
    ("no payload detected", dict(kwargs={"payload_pixels": 0}, mean_confidence=0.9), "hold"),
    ("low payload signal",
     dict(kwargs={"payload": advisor.PAYLOAD_FLOOR / 2}, mean_confidence=0.9), "hold"),
    ("association not measurable",
     dict(kwargs={"liberation": None}, mean_confidence=0.9), "hold"),
    ("marginal band",
     dict(kwargs={"liberation": advisor.LOW_LIBERATION}, mean_confidence=0.9), "hold"),
    ("grind finer",
     dict(kwargs={"liberation": advisor.LOW_LIBERATION - advisor.LIBERATION_MARGIN - 0.05},
          mean_confidence=0.9), "grind"),
    ("depress reject phase",
     dict(kwargs={"payload": 0.35,
                   "extra_roles": {"reject": advisor.REJECT_CEILING + 0.05}},
          mean_confidence=0.9), "grind"),
    ("raise depressant",
     dict(kwargs={"payload": 0.90,
                   "extra_roles": {"deleterious": advisor.DELETERIOUS_CEILING + 0.05}},
          mean_confidence=0.9), "grind"),
    ("continue at setpoint", dict(kwargs={}, mean_confidence=0.9), ""),
]


class TestAdviseOutputsMatchVerdictState:
    @pytest.mark.parametrize("name,call,expected_class", CASES, ids=[c[0] for c in CASES])
    def test_every_real_advise_branch_gets_the_right_verdict_class(
        self, name, call, expected_class
    ):
        result = _result(**call["kwargs"])
        rec = advisor.advise(result, mean_confidence=call["mean_confidence"])
        css_class, label = verdict_state(rec.action)

        assert css_class == expected_class, (
            f"advise() branch {name!r} produced action {rec.action!r}, "
            f"which verdict_state() classified as {css_class!r} (expected "
            f"{expected_class!r}). If advisor.py's action text changed, "
            f"verdict_state()'s prefixes need updating too."
        )
        assert "unrecognised action" not in label, (
            f"advise() branch {name!r} produced {rec.action!r}, which "
            "verdict_state() does not recognise at all - it is falling "
            "through to the fail-safe default rather than being matched "
            "by name. Update verdict_state()'s prefixes."
        )

    def test_every_case_in_this_file_actually_exercises_a_distinct_action(self):
        """Guards against a copy-paste case that silently duplicates another
        branch instead of reaching the one it claims to."""
        actions = set()
        for _name, call, _expected in CASES:
            result = _result(**call["kwargs"])
            rec = advisor.advise(result, mean_confidence=call["mean_confidence"])
            actions.add(rec.action)
        assert len(actions) == len(CASES)
