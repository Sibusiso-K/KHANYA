"""Week-3 conformal coverage and the Week-4 degraded-input placeholder."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from reefprint.trust.conformal import audit_coverage_by_locality, coverage_band
from reefprint.trust.quality import (
    InputQualityMetrics,
    QualityIssue,
    QualityThresholds,
    assess_input_quality,
)


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


def thresholds() -> QualityThresholds:
    return QualityThresholds(
        min_sharpness=0.5,
        max_glare_fraction=0.1,
        max_polish_defect_fraction=0.2,
        min_exposure=0.2,
        max_exposure=0.8,
        min_foreground_fraction=0.1,
        source="synthetic calibration fixture; replace with field calibration",
    )


def good_metrics() -> InputQualityMetrics:
    return InputQualityMetrics(
        sharpness=0.8,
        glare_fraction=0.02,
        polish_defect_fraction=0.05,
        exposure=0.5,
        foreground_fraction=0.7,
    )


def test_good_input_passes_the_quality_gate():
    assessment = assess_input_quality(good_metrics(), thresholds())

    assert assessment.usable
    assert assessment.refusal_reason is None


def test_no_silent_failure_under_degraded_input():
    """**Week-4 gate.** Every degraded input yields a result or a stated refusal."""
    degraded = {
        QualityIssue.DEFOCUS: InputQualityMetrics(0.1, 0.02, 0.05, 0.5, 0.7),
        QualityIssue.GLARE: InputQualityMetrics(0.8, 0.4, 0.05, 0.5, 0.7),
        QualityIssue.POOR_POLISH: InputQualityMetrics(0.8, 0.02, 0.4, 0.5, 0.7),
        QualityIssue.WRONG_EXPOSURE: InputQualityMetrics(0.8, 0.02, 0.05, 0.95, 0.7),
        QualityIssue.EMPTY_FIELD: InputQualityMetrics(0.8, 0.02, 0.05, 0.5, 0.0),
    }

    for expected_issue, metrics in degraded.items():
        assessment = assess_input_quality(metrics, thresholds())
        assert assessment.refused
        assert expected_issue in assessment.issues
        assert assessment.refusal_reason


def test_multiple_quality_failures_are_not_hidden_by_the_first_one():
    assessment = assess_input_quality(
        InputQualityMetrics(0.1, 0.4, 0.4, 0.95, 0.0),
        thresholds(),
    )

    assert set(assessment.issues) == {
        QualityIssue.DEFOCUS,
        QualityIssue.GLARE,
        QualityIssue.POOR_POLISH,
        QualityIssue.WRONG_EXPOSURE,
        QualityIssue.EMPTY_FIELD,
    }
    assert "defocus" in assessment.explain()
    assert "empty field" in assessment.explain()


def test_missing_or_invalid_quality_metadata_is_a_refusal():
    assessment = assess_input_quality(
        InputQualityMetrics(None, 0.02, 0.05, 0.5, 0.7),
        thresholds(),
    )

    assert assessment.issues == (QualityIssue.MALFORMED_INPUT,)
    assert assessment.refusal_reason
