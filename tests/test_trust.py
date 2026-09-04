"""Week-3 conformal coverage and the Week-4 degraded-input placeholder."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from reefprint.trust.conformal import audit_coverage_by_locality, coverage_band


@dataclass(frozen=True, slots=True)
class Unit:
    section_id: str
    locality: str


def units(prefix: str, locality: str, count: int) -> tuple[Unit, ...]:
    return tuple(Unit(f"{prefix}_{index}", locality) for index in range(count))


def calibration_units(count: int = 20, points_per_locality: int = 1) -> tuple[Unit, ...]:
    return tuple(
        unit
        for index in range(count)
        for unit in units(f"cal_{index}", f"cal_{index}", points_per_locality)
    )


def test_conformal_coverage_holds_per_held_out_locality():
    """Week-3 gate: report every held-out locality, not only a pooled proportion."""
    calibration = calibration_units()
    held_out = (*units("test_a", "locality_a", 20), *units("test_b", "locality_b", 20))
    report = audit_coverage_by_locality(
        calibration,
        held_out,
        covered=(True,) * 19 + (False,) + (True,) * 19 + (False,),
    )

    assert [result.locality for result in report.localities] == ["locality_a", "locality_b"]
    assert all(result.coverage == pytest.approx(0.95) for result in report.localities)
    assert report.passes
    assert "locality_a=0.950" in report.summary()
    assert "locality_b=0.950" in report.summary()


def test_a_locality_outside_the_band_fails_the_gate_even_if_the_pool_would_pass():
    calibration = calibration_units()
    held_out = (*units("test_a", "locality_a", 20), *units("test_b", "locality_b", 20))
    report = audit_coverage_by_locality(
        calibration,
        held_out,
        covered=(True,) * 20 + (False,) * 20,
    )

    assert report.localities[0].within_band
    assert not report.localities[1].within_band
    assert not report.passes


def test_reported_coverage_interval_matches_honest_n():
    """The exact Beta law, sized by independent calibration localities."""
    at_100 = coverage_band(100)
    at_20 = coverage_band(20)

    assert at_100.n_calibration == 100
    assert at_100.standard_deviation == pytest.approx(0.0296, abs=0.0001)
    assert at_20.standard_deviation == pytest.approx(0.0626, abs=0.0001)
    assert at_20.standard_deviation > at_100.standard_deviation


def test_held_out_sample_noise_is_combined_with_calibration_uncertainty():
    band = coverage_band(20)

    lower, upper = band.predictive_count_bounds(20)

    assert lower < 20 <= upper
    assert band.contains_observation(20, 20)
    assert not band.contains_observation(0, 20)


def test_pixels_do_not_inflate_the_honest_calibration_n():
    calibration = calibration_units(points_per_locality=20)
    held_out = units("test", "locality_test", 10)

    report = audit_coverage_by_locality(calibration, held_out, covered=(True,) * 10)

    assert report.band.n_calibration == 20


def test_overlapping_calibration_and_test_locality_is_refused():
    calibration = units("cal", "shared", 2) + units("cal2", "other", 2)
    held_out = units("test", "shared", 3)

    with pytest.raises(ValueError, match="shared"):
        audit_coverage_by_locality(calibration, held_out, covered=(True,) * 3)


@pytest.mark.placeholder
def test_no_silent_failure_under_degraded_input():
    """**Week-4 gate.** Every degraded input must produce a result or stated refusal."""
    pytest.fail("NOT BUILT — trust: degraded-input behaviour, week-4 gate")
