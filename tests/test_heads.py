"""Domain heads remain gated; their shared interval-bearing output is implemented."""

from __future__ import annotations

import pytest

from reefprint.heads.entrainment import (
    BoundedFraction,
    entrainment_risk_conservative_default,
    fine_chromite_entrainment_risk,
)
from reefprint.heads.output import HeadEstimate
from reefprint.quantity import assumed, cited, design_target, measured
from reefprint.trust.abstain import Abstention, AbstentionTrigger


def _bounded(value: float, low: float, high: float, source: str) -> BoundedFraction:
    return BoundedFraction(
        quantity=assumed(value, "", source),
        low=assumed(low, "", f"{source} (low)"),
        high=assumed(high, "", f"{source} (high)"),
    )


def test_fine_chromite_entrainment_risk_index():
    """Cr2O3 is the binding constraint on UG2 flotation — gauntlet F4.

    Illustrative values throughout, ``ASSUMED`` and stated as such — the real
    ``entrainment_factor`` and ``water_recovery`` numbers are the domain lead's call (Rule 6),
    not this test's.
    """
    chromite_mass_fraction = _bounded(0.55, 0.50, 0.60, "illustrative segmentation output")
    fine_fraction = _bounded(0.20, 0.15, 0.25, "illustrative grind-curve estimate")
    entrainment_factor = _bounded(0.40, 0.30, 0.50, "illustrative EF(d), Savassi et al. 1998 shape")
    water_recovery = _bounded(0.20, 0.15, 0.25, "illustrative plant water recovery")

    estimate = fine_chromite_entrainment_risk(
        chromite_mass_fraction=chromite_mass_fraction,
        fine_fraction=fine_fraction,
        entrainment_factor=entrainment_factor,
        water_recovery=water_recovery,
    )

    assert estimate.head == "fine_chromite_entrainment_risk"
    assert estimate.estimate.value == pytest.approx(0.55 * 0.20 * 0.40 * 0.20)
    lower, upper = estimate.interval()
    assert lower == pytest.approx(0.50 * 0.15 * 0.30 * 0.15)
    assert upper == pytest.approx(0.60 * 0.25 * 0.50 * 0.25)
    assert lower <= estimate.estimate.value <= upper


def test_the_worst_case_bound_brackets_the_point_estimate_for_any_valid_inputs():
    """The proof in entrainment.py's module docstring, checked rather than only asserted:
    nonnegative factors each inside their own [low, high] compose so the product of lows is
    <= the product of points is <= the product of highs. No statistical assumption involved.
    """
    a = _bounded(0.9, 0.8, 0.95, "a")
    b = _bounded(0.05, 0.01, 0.10, "b")
    c = _bounded(0.99, 0.90, 1.00, "c")
    d = _bounded(0.5, 0.2, 0.8, "d")

    estimate = fine_chromite_entrainment_risk(
        chromite_mass_fraction=a, fine_fraction=b, entrainment_factor=c, water_recovery=d
    )
    lower, upper = estimate.interval()
    assert lower <= estimate.estimate.value <= upper


def test_bounded_fraction_refuses_a_fraction_outside_zero_one_and_an_inverted_range():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        BoundedFraction(
            quantity=assumed(1.4, "", "bad"),
            low=assumed(1.0, "", "bad"),
            high=assumed(1.5, "", "bad"),
        )
    with pytest.raises(ValueError, match="empty or inverted"):
        BoundedFraction(
            quantity=assumed(0.5, "", "bad"),
            low=assumed(0.6, "", "bad"),
            high=assumed(0.4, "", "bad"),
        )


def test_entrainment_head_refuses_a_design_target_input():
    """Rule 1's boundary, ADR-0002: nothing may be derived from a design-target figure.
    ``BoundedFraction`` refuses one immediately at construction, before it could ever reach the
    multiplication in ``fine_chromite_entrainment_risk`` — the earliest point the contamination
    can be caught.
    """
    with pytest.raises(ValueError, match="design target"):
        BoundedFraction(
            quantity=design_target(0.5, "", "0.2-1.6 um/px design range, midpoint"),
            low=design_target(0.4, "", "design range low"),
            high=design_target(0.6, "", "design range high"),
        )


def test_entrainment_risk_abstains_conservatively_high_not_low():
    """Rule 5's worked example, named in trust.abstain's own docstring: entrainment risk is
    ASSUME_HIGH. An abstention must not quietly default to the low, reassuring end.
    """
    default = entrainment_risk_conservative_default(
        low=cited(0.05, "", "plant floor, illustrative"),
        high=cited(0.60, "", "plant ceiling, illustrative"),
        default=cited(0.45, "", "conservative high-side default, illustrative"),
    )
    abstention = Abstention(
        default=default,
        reason="segmentation output failed the input-quality gate: defocus",
        trigger=AbstentionTrigger.DEGRADED_INPUT,
    )
    assert abstention.emit().value == pytest.approx(0.45)

    with pytest.raises(ValueError, match="unsafe side"):
        entrainment_risk_conservative_default(
            low=cited(0.05, "", "plant floor, illustrative"),
            high=cited(0.60, "", "plant ceiling, illustrative"),
            default=cited(0.08, "", "wrongly reassuring low-side default"),
        )


@pytest.mark.placeholder
def test_naturally_floating_gangue_load():
    """Talc/serpentine for depressant dosing.

    Open question 1: detection without SWIR is unproven. Week 2, empirical. If it fails we drop
    to two properties rather than claiming it anyway.
    """
    pytest.fail("NOT BUILT — heads: NFG load")


@pytest.mark.placeholder
def test_stockpile_oxidation_index():
    """Sulphide surfaces tarnish with residence time, destroying floatability.

    Macro-visible, unmeasured anywhere, and the fallback if the falsification test kills the
    texture residual — it does not depend on that residual.
    """
    pytest.fail("NOT BUILT — heads: oxidation index")


def test_every_prediction_carries_a_confidence_interval():
    """Rule 4. A point estimate with no interval is not a result."""
    # This test is intentionally not a placeholder: the domain-specific heads above remain red,
    # but every head that does emit a value must use this common contract.
    estimate = HeadEstimate(
        head="synthetic risk",
        estimate=measured(0.4, "", "synthetic test observation"),
        lower=measured(0.2, "", "synthetic 95% lower bound"),
        upper=measured(0.6, "", "synthetic 95% upper bound"),
        confidence=0.95,
    )
    assert estimate.interval() == (0.2, 0.6)
    with pytest.raises(ValueError, match="inside"):
        HeadEstimate(
            head="bad",
            estimate=measured(0.8, "", "test"),
            lower=measured(0.2, "", "test"),
            upper=measured(0.6, "", "test"),
            confidence=0.95,
        )
