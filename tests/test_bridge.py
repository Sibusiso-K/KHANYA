"""The mask/series boundary, and the three project rules it exists to make unavoidable.

Every test here is one of: N3 (the geometry that inverts to zero anisotropy in silence), N2 (the
noise floor that rises as reflectance falls), or Rule 2 (splits are by locality). The boundary
has no other reason to exist — plumbing this thin would not be worth a module otherwise.
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.phantom import PHASES, crossed_polars_stage_series, synthetic_rotation_series
from reefprint.acquire.series import RotationGeometry, RotationSeries
from reefprint.bridge import (
    LabelledSection,
    LabelProvenance,
    PixelSelection,
    SectionMeasurement,
    group_by_locality,
    measure_section,
    select_pixels,
)

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
# N3 — the geometry check cannot be routed around, because that is exactly how it was routed
# around the first time.
# ---------------------------------------------------------------------------------------------


def test_a_stage_rotation_is_refused_at_the_boundary_rather_than_measured():
    """The failure the boundary was built for.

    A crossed-polars stage rotation modulates at 4*phi. The Stokes model fits 2*theta, the
    projection is zero, and every anisotropic grain comes back isotropic with no error raised.
    The frames here demonstrably modulate, so nothing else in the pipeline would notice.
    """
    stage = crossed_polars_stage_series(n_angles=72, shape=SHAPE, seed=0)
    section = _section(stage.labels)

    assert np.ptp(stage.series.frames, axis=0).max() > 0, "the frames must actually modulate"

    with pytest.raises(ValueError, match="4"):
        measure_section(section, stage.series)


def test_a_series_that_never_recorded_its_geometry_is_refused():
    """UNKNOWN is not "probably fine". Rule 1: do not guess, and do not default to convenient."""
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    unrecorded = RotationSeries(
        frames=phantom.series.frames,
        angles_rad=phantom.series.angles_rad,
        source="a public archive that did not say",
    )
    assert unrecorded.geometry is RotationGeometry.UNKNOWN

    with pytest.raises(ValueError, match="does not record which element rotated"):
        measure_section(_section(phantom.labels), unrecorded)


def test_no_keyword_argument_can_disable_the_geometry_check():
    """A guard with an escape hatch is documentation, not a guard.

    Written as a signature test on purpose: the protection is that ``measure_section`` has no
    parameter capable of turning it off, and that property is easy to erode by adding a
    well-meaning ``strict=False`` later.
    """
    import inspect

    parameters = set(inspect.signature(measure_section).parameters)
    assert parameters == {"section", "series", "min_pixels"}


# ---------------------------------------------------------------------------------------------
# The crash KHANYA hit, turned into data.
# ---------------------------------------------------------------------------------------------


def test_a_mask_frame_shape_mismatch_is_reported_with_both_shapes_not_raised():
    """Dying on the first mismatch hides how many there are, and the count is the diagnosis.

    One bad mask and a systematically transposed archive present identically at the first
    failure and need completely different fixes.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    transposed = _section(np.ascontiguousarray(phantom.labels.T))

    result = measure_section(
        transposed, _analyser_series(phantom.series.frames, phantom.series.angles_rad)
    )

    assert not result.was_measured
    assert result.skipped == "mask/frame shape mismatch"
    assert dict(result.detail) == {"mask_shape": "(256, 192)", "frame_shape": "(192, 256)"}


def test_a_section_with_too_few_angles_is_skipped_rather_than_inverted():
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    two = _analyser_series(phantom.series.frames[:2], phantom.series.angles_rad[:2])

    result = measure_section(_section(phantom.labels), two)

    assert not result.was_measured
    assert "2 angles" in str(result.skipped)


def test_a_mineral_below_the_pixel_floor_is_omitted_rather_than_measured_thinly():
    """A quartile over forty pixels is not a quartile."""
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    result = measure_section(
        _section(phantom.labels),
        _analyser_series(phantom.series.frames, phantom.series.angles_rad),
        min_pixels=10**6,
    )
    assert not result.was_measured
    assert "labelled pixels" in str(result.skipped)


def test_pixels_whose_code_is_absent_from_the_codebook_are_counted_not_dropped():
    """Silently excluding a mineral reads downstream as "that mineral was not present"."""
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    partial = {label: name for label, name in CODEBOOK.items() if label != 4}  # drop chromite
    section = _section(phantom.labels, codebook=partial)

    result = measure_section(
        section, _analyser_series(phantom.series.frames, phantom.series.angles_rad)
    )

    assert result.n_pixels_unlabelled == int((phantom.labels == 4).sum())
    assert result.n_pixels_unlabelled > 0
    assert "chromite" not in result.by_name()


# ---------------------------------------------------------------------------------------------
# The week-1 claim, expressed in the boundary's own vocabulary.
# ---------------------------------------------------------------------------------------------


def test_pentlandite_stays_dark_while_pyrrhotite_lights_up_through_the_bridge():
    """The gate's mineralogical claim, measured the way the joint experiment will measure it.

    Leg (a) already proves the inversion on the phantom. What this adds is that the claim
    survives being routed through a label map rather than read off a ground-truth Stokes image —
    which is the only form in which it can ever be checked against KHANYA's masks.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, noise_pct=0.5, seed=3)
    result = measure_section(
        _section(phantom.labels),
        _analyser_series(phantom.series.frames, phantom.series.angles_rad),
    )
    stats = result.by_name()

    assert result.was_measured
    assert stats["pentlandite"].median_over_floor < 2.0, "cubic pentlandite must read as noise"
    assert stats["pyrrhotite"].median_over_floor > 10.0, "pyrrhotite must clear its floor"
    assert stats["pyrrhotite"].anisotropy_median > 5 * stats["pentlandite"].anisotropy_median


# ---------------------------------------------------------------------------------------------
# N2 — a median without its floor is a brightness measurement wearing a physics label.
# ---------------------------------------------------------------------------------------------


def test_every_mineral_statistic_carries_its_own_noise_floor():
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, noise_pct=0.5, seed=1)
    result = measure_section(
        _section(phantom.labels),
        _analyser_series(phantom.series.frames, phantom.series.angles_rad),
    )
    assert result.per_mineral
    for stat in result.per_mineral:
        assert np.isfinite(stat.noise_floor_median)
        assert stat.noise_floor_median > 0.0


def test_the_noise_floor_rises_as_reflectance_falls():
    """N2's actual law, on two phases that are both exactly cubic.

    Pentlandite (R = 50%) and chromite (R = 13%) have identical true anisotropy — zero. If the
    reported floor did not track reflectance, one fixed threshold would look defensible, and it
    is not: the darker phase reads the larger apparent anisotropy for purely statistical
    reasons.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, noise_pct=0.5, seed=2)
    stats = measure_section(
        _section(phantom.labels),
        _analyser_series(phantom.series.frames, phantom.series.angles_rad),
    ).by_name()

    bright, dark = stats["pentlandite"], stats["chromite"]
    reflectance_ratio = bright.s0_median / dark.s0_median

    assert dark.noise_floor_median > bright.noise_floor_median
    assert dark.anisotropy_median > bright.anisotropy_median, (
        "the darker cubic phase must read the *larger* apparent anisotropy — that is the trap"
    )
    # The floor goes as 1/S0, so the ratio of floors should track the ratio of reflectances.
    floor_ratio = dark.noise_floor_median / bright.noise_floor_median
    assert floor_ratio == pytest.approx(reflectance_ratio, rel=0.25)
    # And in floor units the two cubic phases become comparable again, which is the point.
    assert dark.median_over_floor == pytest.approx(bright.median_over_floor, rel=0.5)


# ---------------------------------------------------------------------------------------------
# Rule 2 — locality is not optional metadata.
# ---------------------------------------------------------------------------------------------


def test_a_section_without_a_locality_cannot_be_built():
    with pytest.raises(ValueError, match="Rule 2"):
        _section(np.zeros(SHAPE, dtype=np.int16), locality="")


def test_ground_truth_and_predicted_labels_cannot_be_grouped_together():
    """Their average describes neither the minerals nor the model."""
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    series = _analyser_series(phantom.series.frames, phantom.series.angles_rad)
    truth = measure_section(_section(phantom.labels), series)
    predicted = measure_section(
        _section(phantom.labels, section_id="p2", provenance=LabelProvenance.PREDICTED), series
    )

    assert group_by_locality([truth])  # each alone is fine
    assert group_by_locality([predicted])
    with pytest.raises(ValueError, match="GROUND_TRUTH, PREDICTED"):
        group_by_locality([truth, predicted])


def test_grouping_keys_on_locality_not_on_section():
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, seed=0)
    series = _analyser_series(phantom.series.frames, phantom.series.angles_rad)
    merensky = [
        measure_section(_section(phantom.labels, section_id=f"m{i}", locality="Merensky"), series)
        for i in range(3)
    ]
    ug2 = measure_section(_section(phantom.labels, section_id="u1", locality="UG2"), series)

    grouped = group_by_locality([*merensky, ug2])

    assert set(grouped) == {"Merensky", "UG2"}
    assert len(grouped["Merensky"]) == 3


def test_skipped_sections_are_dropped_from_grouping_but_not_from_the_caller_s_list():
    skipped = SectionMeasurement(
        section_id="bad",
        locality="Norilsk",
        provenance=LabelProvenance.GROUND_TRUTH,
        geometry=RotationGeometry.ANALYSER,
        n_angles=72,
        per_mineral=(),
        n_pixels_measured=0,
        n_pixels_unlabelled=0,
        skipped="mask/frame shape mismatch",
    )
    assert group_by_locality([skipped]) == {}


# ---------------------------------------------------------------------------------------------
# Selection — the memory story, and that it does not change the answer.
# ---------------------------------------------------------------------------------------------


def test_selecting_pixels_preserves_the_label_at_every_position():
    phantom = synthetic_rotation_series(n_angles=12, shape=SHAPE, seed=0)
    section = _section(phantom.labels)

    selection = select_pixels(section, rng=np.random.default_rng(0))

    assert selection is not None
    assert np.array_equal(
        selection.section.labels.ravel(), phantom.labels[selection.ys, selection.xs]
    )


def test_a_subsampled_selection_reaches_the_same_verdict_as_the_full_section():
    """The whole point of sampling: 5.0 GB of frames need never exist at once.

    Only the ordering of the mineralogical claim has to survive, not the third decimal place —
    a sample of 1200 pixels per mineral is a distribution estimate, not a census.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=SHAPE, noise_pct=0.5, seed=5)
    section = _section(phantom.labels)
    full = measure_section(
        section, _analyser_series(phantom.series.frames, phantom.series.angles_rad)
    ).by_name()

    selection = select_pixels(section, rng=np.random.default_rng(5))
    assert selection is not None
    sampled_frames = np.stack([selection.read_from(f) for f in phantom.series.frames])[:, None, :]
    sampled = measure_section(
        selection.section,
        _analyser_series(sampled_frames, phantom.series.angles_rad),
    ).by_name()

    assert set(sampled) == set(full)
    assert sampled["pentlandite"].median_over_floor < 2.0
    assert sampled["pyrrhotite"].median_over_floor > 10.0
    for name, stat in sampled.items():
        assert stat.anisotropy_median == pytest.approx(full[name].anisotropy_median, abs=0.01), name


def test_reading_a_selection_out_of_a_transposed_frame_names_the_disagreement():
    """The same mismatch as above, caught on the path where no series carries the shape."""
    phantom = synthetic_rotation_series(n_angles=12, shape=SHAPE, seed=0)
    selection = select_pixels(_section(phantom.labels), rng=np.random.default_rng(0))
    assert selection is not None

    with pytest.raises(ValueError, match="transposed"):
        selection.read_from(np.zeros((SHAPE[1], SHAPE[0])))


def test_a_selection_whose_positions_do_not_match_its_labels_cannot_be_built():
    with pytest.raises(ValueError, match=r"\(1, 3\)"):
        PixelSelection(
            ys=np.array([0, 1, 2]),
            xs=np.array([0, 1, 2]),
            section=_section(np.zeros((1, 5), dtype=np.int16)),
        )


def test_an_empty_section_yields_no_selection_rather_than_an_error():
    """A public archive full of unlabelled sections is a normal Tuesday, not an exception."""
    empty = _section(np.full(SHAPE, 99, dtype=np.int16))  # code 99 is not in the codebook
    assert select_pixels(empty, rng=np.random.default_rng(0)) is None


def test_an_unknown_mineral_name_raises_rather_than_returning_an_empty_mask():
    """An all-false mask reads as "absent from this section", which is a different claim."""
    phantom = synthetic_rotation_series(n_angles=12, shape=SHAPE, seed=0)
    with pytest.raises(KeyError, match="pentlandiet"):
        _section(phantom.labels).mineral_mask("pentlandiet")
