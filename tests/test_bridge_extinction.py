"""The mask/series boundary for the fourth-harmonic fallback — leg (b)'s path if N3 is confirmed.

Mirrors ``tests/test_bridge.py``, geometry for geometry: everywhere ``measure_section`` requires
:data:`RotationGeometry.ANALYSER` and refuses :data:`SPECIMEN`, ``measure_section_extinction`
requires :data:`SPECIMEN` and refuses :data:`ANALYSER`. Two guards, one shape, so that whichever
geometry a real archive turns out to be, the wrong estimator cannot be run on it by accident
either way.
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.phantom import PHASES, crossed_polars_stage_series
from reefprint.acquire.series import RotationGeometry, RotationSeries
from reefprint.bridge.extinction import measure_section_extinction
from reefprint.bridge.section import LabelledSection, LabelProvenance

CODEBOOK = {phase.label: phase.name for phase in PHASES}
SHAPE = (192, 256)


def _section(
    labels: np.ndarray,
    *,
    section_id: str = "phantom_01",
    locality: str = "phantom",
    provenance: LabelProvenance = LabelProvenance.GROUND_TRUTH,
    codebook: dict[int, str] | None = None,
) -> LabelledSection:
    return LabelledSection(
        labels=labels,
        codebook=CODEBOOK if codebook is None else codebook,
        section_id=section_id,
        locality=locality,
        provenance=provenance,
    )


def _analyser_series(frames: np.ndarray, angles: np.ndarray) -> RotationSeries:
    return RotationSeries(
        frames=frames,
        angles_rad=angles,
        source="test",
        geometry=RotationGeometry.ANALYSER,
    )


# ---------------------------------------------------------------------------------------------
# N3's mirror image: an analyser series fed to the extinction estimator is the same class of
# mistake as a stage series fed to the Stokes inversion, just in the other direction.
# ---------------------------------------------------------------------------------------------


def test_an_analyser_series_is_refused_at_the_extinction_boundary():
    stage = crossed_polars_stage_series(n_angles=12, shape=(16, 16), grains_per_phase=1, seed=0)
    wrong_geometry = _analyser_series(stage.series.frames, stage.series.angles_rad)
    section = _section(stage.labels)

    with pytest.raises(ValueError, match="rotating the analyser"):
        measure_section_extinction(section, wrong_geometry)


def test_a_series_that_never_recorded_its_geometry_is_refused_at_the_extinction_boundary():
    stage = crossed_polars_stage_series(n_angles=12, shape=(16, 16), grains_per_phase=1, seed=0)
    unknown = RotationSeries(
        frames=stage.series.frames, angles_rad=stage.series.angles_rad, source="test"
    )
    section = _section(stage.labels)

    with pytest.raises(ValueError, match="does not record which element rotated"):
        measure_section_extinction(section, unknown)


def test_no_keyword_argument_can_disable_the_geometry_check():
    import inspect

    assert "geometry" not in inspect.signature(measure_section_extinction).parameters
    assert "skip_geometry_check" not in inspect.signature(measure_section_extinction).parameters


# ---------------------------------------------------------------------------------------------
# Per-section defects: skipped, not raised — same asymmetry as measure_section, same reason.
# ---------------------------------------------------------------------------------------------


def test_a_mask_frame_shape_mismatch_is_reported_with_both_shapes_not_raised():
    stage = crossed_polars_stage_series(n_angles=12, shape=(16, 16), grains_per_phase=1, seed=0)
    section = _section(np.zeros((20, 20), dtype=int))

    result = measure_section_extinction(section, stage.series)

    assert result.skipped is not None
    assert "shape" in result.skipped
    detail = dict(result.detail)
    assert detail["mask_shape"] == str((20, 20))
    assert detail["frame_shape"] == str((16, 16))


def test_a_section_with_too_few_angles_is_skipped_rather_than_inverted():
    stage = crossed_polars_stage_series(n_angles=2, shape=(16, 16), grains_per_phase=1, seed=0)
    section = _section(stage.labels)

    result = measure_section_extinction(section, stage.series)

    assert result.skipped is not None
    assert "angles" in result.skipped


def test_a_mineral_below_the_pixel_floor_is_omitted_rather_than_measured_thinly():
    stage = crossed_polars_stage_series(n_angles=12, shape=(16, 16), grains_per_phase=1, seed=0)
    section = _section(stage.labels)

    result = measure_section_extinction(section, stage.series, min_pixels=1_000_000)

    assert result.skipped is not None
    assert "labelled pixels" in result.skipped


# ---------------------------------------------------------------------------------------------
# The mineralogical payoff: pentlandite is exactly dark, pyrrhotite extincts. Same claim the
# Stokes path makes, recovered through the other geometry's own physics.
# ---------------------------------------------------------------------------------------------


def test_pentlandite_reads_near_zero_extinction_depth_while_pyrrhotite_extincts():
    stage = crossed_polars_stage_series(
        n_angles=72, shape=SHAPE, grains_per_phase=6, noise_pct=0.0, seed=1
    )
    section = _section(stage.labels)

    result = measure_section_extinction(section, stage.series)

    assert result.skipped is None
    by_name = result.by_name()
    assert by_name["pentlandite"].extinction_depth_median == pytest.approx(0.0, abs=1e-9)
    assert by_name["pyrrhotite"].extinction_depth_median > 0.0


def test_every_mineral_statistic_carries_a_crossing_ratio():
    stage = crossed_polars_stage_series(
        n_angles=72, shape=SHAPE, grains_per_phase=6, noise_pct=0.0, seed=1
    )
    section = _section(stage.labels)

    result = measure_section_extinction(section, stage.series)

    for stat in result.per_mineral:
        assert stat.crossing_ratio_median >= 0.0


def test_geometry_is_recorded_on_the_result_even_when_skipped():
    stage = crossed_polars_stage_series(n_angles=2, shape=(16, 16), grains_per_phase=1, seed=0)
    section = _section(stage.labels)

    result = measure_section_extinction(section, stage.series)

    assert result.geometry is RotationGeometry.SPECIMEN
