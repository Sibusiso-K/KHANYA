"""The decision layer, tested in the order the failures actually matter.

The advisor's whole reason to exist is that a model can score well on aggregate
accuracy while missing the sub-1% phase that carries the value. The branch
order below is payload-first for that reason, and these tests pin it: an
unmeasured field must never fall through to a confident operational
instruction.
"""
import pytest

from src import advisor
from src.modal import ModalResult


def _result(liberation=0.9, payload=0.05, ore_area=0.8, n_particles=12,
            payload_pixels=500, n_payload_particles=12):
    """A ModalResult with healthy defaults; override one field per test."""
    return ModalResult(
        phase_fractions={"chalcopyrite": payload, "pyrite": 1.0 - payload},
        role_fractions={"payload": payload, "gangue": 1.0 - payload},
        ore_area_fraction=ore_area,
        liberation=liberation,
        n_particles=n_particles,
        payload_pixels=payload_pixels,
        n_payload_particles=n_payload_particles,
    )


class TestRefusals:
    """Every one of these must refuse. None may return an operational action."""

    def test_insufficient_ore_refuses(self):
        rec = advisor.advise(_result(ore_area=0.01), mean_confidence=0.99)
        assert "No recommendation" in rec.action

    def test_no_payload_detected_is_flagged_not_treated_as_zero_grade(self):
        """Absence of detection is not absence of mineral."""
        rec = advisor.advise(_result(payload_pixels=0), mean_confidence=0.99)
        assert "no payload detected" in rec.action.lower()
        assert "manual review" in rec.action.lower()

    def test_payload_below_the_floor_is_flagged(self):
        rec = advisor.advise(
            _result(payload=advisor.PAYLOAD_FLOOR / 2), mean_confidence=0.99
        )
        assert "low payload signal" in rec.action.lower()

    def test_unmeasurable_liberation_is_flagged_not_guessed(self):
        rec = advisor.advise(_result(liberation=None), mean_confidence=0.99)
        assert "not measurable" in rec.action.lower()

    def test_refusals_win_over_a_confident_liberation_number(self):
        """Ordering matters: a field with no ore must refuse even when
        liberation looks decisive. The checks are payload-first on purpose."""
        rec = advisor.advise(
            _result(ore_area=0.001, liberation=0.99), mean_confidence=0.99
        )
        assert "No recommendation" in rec.action


class TestLiberationBoundary:
    def test_inside_the_band_the_field_does_not_decide(self):
        rec = advisor.advise(
            _result(liberation=advisor.LOW_LIBERATION), mean_confidence=0.99
        )
        assert "Marginal" in rec.action

    def test_clearly_below_the_floor_says_grind_finer(self):
        below = advisor.LOW_LIBERATION - advisor.LIBERATION_MARGIN - 0.05
        rec = advisor.advise(_result(liberation=below), mean_confidence=0.99)
        assert rec.action == "Grind finer"

    def test_the_band_is_symmetric_about_the_floor(self):
        """Both sides of the threshold, equally far out, must hedge or not
        hedge together - an asymmetric band is a silent bias in the circuit."""
        margin = advisor.LIBERATION_MARGIN
        just_inside_low = advisor.LOW_LIBERATION - margin * 0.5
        just_inside_high = advisor.LOW_LIBERATION + margin * 0.5
        low = advisor.advise(_result(liberation=just_inside_low), 0.99)
        high = advisor.advise(_result(liberation=just_inside_high), 0.99)
        assert "Marginal" in low.action
        assert "Marginal" in high.action

    def test_a_zero_margin_removes_the_hedge(self):
        """Ground-truth masks are passed with margin 0.0 - an annotation
        carries no estimator error, so banding it would hide the very
        disagreement the decision-gap experiment measures."""
        rec = advisor.advise(
            _result(liberation=advisor.LOW_LIBERATION - 0.01),
            mean_confidence=0.99,
            liberation_margin=0.0,
        )
        assert rec.action == "Grind finer"


class TestConfidenceReporting:
    @pytest.mark.parametrize("score,expected", [(0.85, "high"), (0.84, "low")])
    def test_confidence_threshold_sits_at_85_percent(self, score, expected):
        rec = advisor.advise(_result(), mean_confidence=score)
        assert rec.confidence.startswith(expected)

    def test_low_confidence_tells_the_operator_what_to_do(self):
        rec = advisor.advise(_result(), mean_confidence=0.10)
        assert "verify manually" in rec.confidence

    def test_every_recommendation_carries_a_reason(self):
        """A bare verdict is not actionable and not auditable."""
        for kwargs in ({}, {"ore_area": 0.001}, {"payload_pixels": 0},
                       {"liberation": None}):
            rec = advisor.advise(_result(**kwargs), mean_confidence=0.9)
            assert rec.reason.strip()


class TestEvidenceSufficiency:
    """An association index from a handful of particles cannot decide a plant action."""

    def test_floor_is_a_provisional_policy_and_says_so(self):
        assert advisor.MIN_PAYLOAD_PARTICLES == 9
        rec = advisor.advise(_result(liberation=0.0, n_payload_particles=2), 0.99)
        assert "provisional floor of 9" in rec.reason
        assert "not a statistical bound" in rec.reason
        assert "perfect segmentation" not in rec.reason

    @pytest.mark.parametrize("liberation", [0.0, 0.95])
    def test_too_few_payload_particles_refuses_either_way(self, liberation):
        rec = advisor.advise(_result(liberation=liberation, n_payload_particles=2), 0.99)
        assert rec.action == "No recommendation - too few payload particles"
        assert "only 2" in rec.reason

    def test_unmeasured_count_fails_closed(self):
        rec = advisor.advise(_result(liberation=0.0, n_payload_particles=None), 0.99)
        assert rec.action == "No recommendation - too few payload particles"

    def test_the_threshold_itself_is_enough(self):
        rec = advisor.advise(
            _result(liberation=0.0, n_payload_particles=advisor.MIN_PAYLOAD_PARTICLES), 0.99)
        assert rec.action == "Grind finer"

    def test_the_refusal_is_an_abstention_the_plant_holds_on(self):
        from dashboard.control import command_for
        rec = advisor.advise(_result(liberation=0.0, n_payload_particles=2), 0.99)
        assert advisor.verdict_state(rec.action)[0] == "hold"
        assert command_for(rec.action)[0] is None
