"""Domain heads remain gated; their shared interval-bearing output is implemented."""

from __future__ import annotations

import pytest

from reefprint.heads.output import HeadEstimate
from reefprint.quantity import measured

@pytest.mark.placeholder
def test_fine_chromite_entrainment_risk_index():
    """Cr2O3 is the binding constraint on UG2 flotation — gauntlet F4."""
    pytest.fail("NOT BUILT — heads: entrainment risk index")


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
