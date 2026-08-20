"""Rule 1, made structural: never invent a number; flag every assumption as an assumption.

The hardest of the standing rules to enforce, because an invented number and a measured one are
the same 64 bits. There is no malformed state to detect. `0.35` is `0.35` whether it came from
a calibration run, a textbook, a phantom, a plausible guess, or a specification for hardware
that was never built.

So the guard cannot be a check on the value. It has to be a property carried *with* the value,
and it has to be contagious: the moment an assumption enters a calculation, everything
downstream of it is an assumption too. That is the part prose never gets right, because the
contamination happens three functions away from where the assumption was written down.
"""

from __future__ import annotations

import re

import pytest

from reefprint.quantity import (
    Provenance,
    Quantity,
    assumed,
    cited,
    design_target,
    measured,
    require_reportable,
    stipulated,
)

# --------------------------------------------------------------------------------------
# A number has to say where it came from
# --------------------------------------------------------------------------------------


def test_a_quantity_must_say_where_its_number_came_from():
    """Rule 1's second clause, as a refusal. An unsourced number is the thing being banned."""
    with pytest.raises(ValueError, match="source"):
        Quantity(value=0.35, unit="um/px", provenance=Provenance.ASSUMED, source="")


def test_a_whitespace_source_does_not_count_as_a_source():
    with pytest.raises(ValueError, match="source"):
        measured(40.4, "x", "   ")


def test_a_measured_quantity_constructs_and_keeps_its_provenance():
    q = measured(40.4, "x", "experiments/001-week1-gate, phantom inversion")

    assert q.value == pytest.approx(40.4)
    assert q.provenance is Provenance.MEASURED


def test_a_nan_is_refused_because_it_is_a_number_that_was_never_measured():
    with pytest.raises(ValueError, match="finite"):
        measured(float("nan"), "um", "grain long axis")


def test_an_infinity_is_refused_for_the_same_reason():
    with pytest.raises(ValueError, match="finite"):
        cited(float("inf"), "percent", "Craig & Vaughan table 3.1")


# --------------------------------------------------------------------------------------
# The provenance is contagious
# --------------------------------------------------------------------------------------


def test_an_assumption_contaminates_everything_it_touches():
    """The failure rule 1 exists to prevent, stated as an assertion.

    A measured grain length times an assumed scale is not a measured grain size. It is an
    assumption wearing a measurement's units, and three functions downstream nothing says so.
    """
    grains = measured(47.0, "px", "grain long axis, S2_01")
    scale = assumed(0.35, "um/px", "typical for a 4x objective; not measured")

    size = grains * scale

    assert size.provenance is Provenance.ASSUMED


def test_the_weaker_provenance_wins_regardless_of_which_side_it_is_on():
    strong = measured(2.0, "um", "bridge/measure.py")
    weak = assumed(3.0, "um", "plausible for UG2 BMS")

    assert (strong + weak).provenance is Provenance.ASSUMED
    assert (weak + strong).provenance is Provenance.ASSUMED


def test_two_measured_quantities_stay_measured():
    a = measured(2.0, "um", "bridge/measure.py on S2_01")
    b = measured(3.0, "um", "bridge/measure.py on S2_02")

    assert (a + b).provenance is Provenance.MEASURED


def test_a_cited_value_is_weaker_than_a_measurement_but_stronger_than_an_assumption():
    assert Provenance.MEASURED.is_stronger_than(Provenance.CITED)
    assert Provenance.CITED.is_stronger_than(Provenance.ASSUMED)


def test_a_design_target_is_the_weakest_thing_there_is():
    for other in (
        Provenance.MEASURED,
        Provenance.CITED,
        Provenance.STIPULATED,
        Provenance.ASSUMED,
    ):
        assert other.is_stronger_than(Provenance.DESIGN_TARGET)


def test_a_stipulated_phantom_value_does_not_become_a_measurement():
    """Experiment 001's ground truth is exactly true of the phantom and of nothing else."""
    phantom = stipulated(0.40, "", "phantom r1, experiments/001-week1-gate")
    real = measured(0.354, "", "bridge/measure.py on S2_01")

    assert (phantom / real).provenance is Provenance.STIPULATED


# --------------------------------------------------------------------------------------
# ADR-0002: nothing may be derived from the design target
# --------------------------------------------------------------------------------------


def test_a_design_target_cannot_escape_the_type():
    """``float()`` is the obvious way around a wrapper. It is closed for this one case."""
    q = design_target(1.6, "um/px", "CLAUDE.md 0.2-1.6 um/px, rig that was never built")

    with pytest.raises(ValueError, match="ADR-0002"):
        float(q)


def test_an_assumption_can_escape_because_it_has_already_been_flagged():
    """Rule 1 permits assumptions. It requires them to be labelled, which this one is."""
    q = assumed(0.35, "um/px", "typical for a 4x objective; not measured")

    assert float(q) == pytest.approx(0.35)


def test_a_measured_quantity_is_reportable():
    require_reportable(measured(40.4, "x", "experiments/001-week1-gate"))


def test_a_flagged_assumption_is_reportable_because_it_is_flagged():
    require_reportable(assumed(0.35, "um/px", "typical for a 4x objective"))


def test_anything_derived_from_the_design_target_is_refused_at_the_boundary():
    grains = measured(47.0, "px", "grain long axis, S2_01")
    scale = design_target(1.6, "um/px", "CLAUDE.md 0.2-1.6 um/px")

    with pytest.raises(ValueError, match="ADR-0002"):
        require_reportable(grains * scale)


def test_the_refusal_names_the_source_that_poisoned_the_calculation():
    """Otherwise the guard tells you there is a problem three functions from where it is."""
    grains = measured(47.0, "px", "grain long axis, S2_01")
    scale = design_target(1.6, "um/px", "CLAUDE.md 0.2-1.6 um/px")

    with pytest.raises(ValueError, match=re.escape("CLAUDE.md 0.2-1.6 um/px")):
        require_reportable(grains * scale)


def test_the_design_target_spans_a_factor_of_eight_so_it_is_not_a_number():
    """Why ADR-0002 says *nothing* may be derived from it, rather than "cite it carefully".

    0.2 and 1.6 um/px are both the design target. A grain size derived from it is not a
    measurement with wide error bars; it is a figure that could be 9 um or 75 um, presented
    to three significant figures.
    """
    grains = measured(47.0, "px", "grain long axis, S2_01")

    low = grains * design_target(0.2, "um/px", "CLAUDE.md design target, fine end")
    high = grains * design_target(1.6, "um/px", "CLAUDE.md design target, coarse end")

    assert high.value / low.value == pytest.approx(8.0)
    assert low.unit == "um"
    for quantity in (low, high):
        with pytest.raises(ValueError, match="ADR-0002"):
            require_reportable(quantity)


# --------------------------------------------------------------------------------------
# A bare float has no provenance, so it cannot join in
# --------------------------------------------------------------------------------------


def test_a_bare_float_cannot_be_added_to_a_quantity():
    """The unlabelled literal is exactly the thing rule 1 is about."""
    with pytest.raises(TypeError):
        measured(1.0, "um", "bridge/measure.py") + 2.0  # type: ignore[operator]


def test_a_bare_float_cannot_be_multiplied_into_a_quantity():
    with pytest.raises(TypeError):
        measured(1.0, "um", "bridge/measure.py") * 2.0  # type: ignore[operator]


# --------------------------------------------------------------------------------------
# Units, because a scale factor is where invented numbers enter
# --------------------------------------------------------------------------------------


def test_adding_quantities_in_different_units_is_refused():
    with pytest.raises(ValueError, match="unit"):
        measured(1.0, "um", "a source") + measured(1.0, "px", "another source")


def test_multiplying_cancels_a_matching_denominator():
    size = measured(47.0, "px", "grain long axis") * assumed(0.35, "um/px", "4x objective")

    assert size.unit == "um"
    assert size.value == pytest.approx(16.45)


def test_multiplying_without_cancellation_composes_the_units():
    area = measured(2.0, "um", "a source") * measured(3.0, "um", "another source")

    assert area.unit == "um*um"


def test_dividing_produces_a_ratio_unit():
    scale = measured(10.0, "um", "a source") / measured(2.0, "px", "another source")

    assert scale.unit == "um/px"


def test_a_ratio_of_like_units_is_dimensionless():
    ratio = measured(10.0, "um", "a source") / measured(2.0, "um", "another source")

    assert ratio.unit == ""


# --------------------------------------------------------------------------------------
# The docs half of the rule: "in the code and in the docs"
# --------------------------------------------------------------------------------------


def test_an_assumption_is_described_as_an_assumption_in_words():
    q = assumed(0.35, "um/px", "typical for a 4x objective; not measured")

    citation = q.cite()

    assert "assumption" in citation.lower()
    assert "typical for a 4x objective" in citation


def test_a_measurement_is_not_described_as_an_assumption():
    q = measured(40.4, "x", "experiments/001-week1-gate")

    assert "assumption" not in q.cite().lower()


def test_a_derived_quantity_carries_every_source_that_fed_it():
    """The contamination is only traceable if the trail survives the arithmetic."""
    grains = measured(47.0, "px", "grain long axis, S2_01")
    scale = assumed(0.35, "um/px", "typical for a 4x objective")

    citation = (grains * scale).cite()

    assert "grain long axis, S2_01" in citation
    assert "typical for a 4x objective" in citation


def test_a_repeated_source_is_named_once():
    a = measured(1.0, "um", "bridge/measure.py on S2_01")
    b = measured(2.0, "um", "bridge/measure.py on S2_01")

    assert (a + b).cite().count("bridge/measure.py on S2_01") == 1


def test_subtracting_keeps_the_weaker_provenance():
    """The pair of ``+``. A guard with a hole gets worked around with bare floats."""
    a = measured(5.0, "um", "bridge/measure.py on S2_01")
    b = assumed(2.0, "um", "plausible rim thickness for UG2 BMS")

    difference = a - b

    assert difference.value == pytest.approx(3.0)
    assert difference.provenance is Provenance.ASSUMED
