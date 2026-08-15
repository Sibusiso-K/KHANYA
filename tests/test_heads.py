"""Placeholder — reefprint.heads. The three visible properties."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_fine_chromite_entrainment_risk_index():
    """Cr2O3 is the binding constraint on UG2 flotation — gauntlet F4."""
    pytest.fail("NOT BUILT — heads: entrainment risk index")


def test_naturally_floating_gangue_load():
    """Talc/serpentine for depressant dosing.

    Open question 1: detection without SWIR is unproven. Week 2, empirical. If it fails we drop
    to two properties rather than claiming it anyway.
    """
    pytest.fail("NOT BUILT — heads: NFG load")


def test_stockpile_oxidation_index():
    """Sulphide surfaces tarnish with residence time, destroying floatability.

    Macro-visible, unmeasured anywhere, and the fallback if the falsification test kills the
    texture residual — it does not depend on that residual.
    """
    pytest.fail("NOT BUILT — heads: oxidation index")


def test_every_prediction_carries_a_confidence_interval():
    """Rule 4. A point estimate with no interval is not a result."""
    pytest.fail("NOT BUILT — heads: intervals on every output")
