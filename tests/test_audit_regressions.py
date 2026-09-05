"""Boundary failures found during the September project audit."""

from dataclasses import dataclass

import numpy as np
import pytest

from reefprint.polarim.extinction import extinction_from_stage_series
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.trust.quality import (
    InputQualityMetrics,
    QualityIssue,
    QualityThresholds,
    assess_input_quality,
)
from reefprint.trust.split import require_locality_disjoint
from reefprint.viz.demo import offline_demo


@pytest.mark.parametrize("inverter", [stokes_from_rotation_series, extinction_from_stage_series])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf")])
def test_nonfinite_pixels_refuse_instead_of_returning_plausible_maps(inverter, invalid):
    frames = np.ones((12, 2, 2))
    frames[0, 0, 0] = invalid
    with pytest.raises(ValueError, match="finite"):
        inverter(frames, np.linspace(0, np.pi, 12, endpoint=False))


@pytest.mark.parametrize("inverter", [stokes_from_rotation_series, extinction_from_stage_series])
def test_nonfinite_angles_are_rejected_before_linear_algebra(inverter):
    with pytest.raises(ValueError, match="finite"):
        inverter(np.ones((3, 2, 2)), np.array([0, 0.5, np.nan]))


def test_manual_split_cannot_relabel_the_same_section_to_hide_leakage():
    @dataclass
    class Unit:
        section_id: str
        locality: str

    with pytest.raises(ValueError, match="two localities"):
        require_locality_disjoint([Unit("same", "A")], [Unit("same", "B")])


@pytest.mark.parametrize("invalid", ["bad", True, None])
def test_malformed_quality_metadata_is_a_structured_refusal(invalid):
    thresholds = QualityThresholds(1, 0.1, 0.1, 0.2, 0.8, 0.1, "synthetic test limits")
    metrics = InputQualityMetrics(invalid, 0, 0, 0.5, 0.5)
    assessment = assess_input_quality(metrics, thresholds)
    assert assessment.refused
    assert assessment.issues == (QualityIssue.MALFORMED_INPUT,)


def test_demo_runs_the_geometry_guard_and_labels_assumptions(monkeypatch):
    from reefprint.acquire.series import RotationGeometry, RotationSeries

    original = RotationSeries.require_analyser_rotation
    calls = []

    def observed_guard(series) -> RotationSeries:
        calls.append(series.geometry)
        return original(series)

    monkeypatch.setattr(RotationSeries, "require_analyser_rotation", observed_guard)
    demo = offline_demo()
    assert calls == [RotationGeometry.ANALYSER, RotationGeometry.UNKNOWN]
    assert "synthetic" in demo.gate.texts[0].get_text()
    text = "\n".join(item.get_text() for item in demo.refusal.texts)
    assert "synthetic input" in text
    assert "does not record" in text
    assert "Source:" in text
    assert "fine-chromite entrainment risk" in text
