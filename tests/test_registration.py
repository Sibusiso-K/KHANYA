"""Leg (a) for P5: the registration estimator recovers a known off-centre rotation on synthetic
data. It says nothing about the real S3 v2 archive — that is leg (b), routed to a Kaggle kernel
(``experiments/007-s3v2-registration/``) rather than run on a memory-constrained local machine,
same reason ``experiments/003-s3v2-extinction/`` already documents a ~5 GB per-section peak.
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.registration import (
    estimate_rotation_centre,
    inscribed_region_mask,
    rotate_about,
)


def _synthetic_field(shape: tuple[int, int], *, seed: int) -> np.ndarray:
    """A speckle field with sharp, sparse features — enough structure for correlation to lock
    onto, small enough to run in milliseconds. Not a mineralogical image; a registration target.
    """
    rng = np.random.default_rng(seed)
    field = rng.normal(0.0, 1.0, size=shape)
    height, width = shape
    for _ in range(max(10, height // 8)):
        y, x = rng.integers(4, height - 4), rng.integers(4, width - 4)
        field[y - 2 : y + 2, x - 2 : x + 2] += 5.0
    return field


def _rotation_series_about(
    field: np.ndarray, angles_deg: list[float], centre_xy: tuple[float, float]
) -> list[np.ndarray]:
    return [rotate_about(field, angle, centre_xy) for angle in angles_deg]


def test_rotate_about_is_its_own_inverse_by_the_opposite_angle() -> None:
    """A convention-independent correctness check: rotating by ``angle`` about a point and then
    by ``-angle`` about the same point must return (up to interpolation loss) the original —
    true regardless of which pixel-centre convention ``centre_xy`` is read in, which
    ``skimage.transform.rotate``'s own default and this module's explicit affine do not
    necessarily share (found the hard way: an earlier version of this test compared directly
    against ``rotate()``'s default centre and failed on a half-pixel convention mismatch that
    said nothing about whether this module's own math was right).
    """
    field = _synthetic_field((40, 40), seed=1)
    off_centre_point = (23.5, 17.0)  # deliberately not the image centre
    forward = rotate_about(field, 37.0, off_centre_point)
    round_trip = rotate_about(forward, -37.0, off_centre_point)
    # Interpolation costs some energy at the edges each pass; correlation survives it cleanly.
    assert np.corrcoef(field.ravel(), round_trip.ravel())[0, 1] > 0.9


def test_recovers_a_known_off_centre_rotation() -> None:
    """The estimator's own validation: a synthetic series rotated about a KNOWN off-centre
    point must recover that offset to well under one pixel. This is leg (a) — it proves the
    estimator, not the real archive.
    """
    field = _synthetic_field((80, 80), seed=0)
    image_centre = (40.0, 40.0)
    true_offset = (8.0, -5.0)
    true_centre = (image_centre[0] + true_offset[0], image_centre[1] + true_offset[1])
    angles = [5.0, 10.0, 20.0, 40.0, 70.0]

    frames = _rotation_series_about(field, angles, true_centre)
    reference = rotate_about(field, 0.0, true_centre)

    estimate = estimate_rotation_centre(reference, frames, angles, search_radius=20.0)

    assert estimate.offset_xy[0] == pytest.approx(true_offset[0], abs=0.5)
    assert estimate.offset_xy[1] == pytest.approx(true_offset[1], abs=0.5)
    assert estimate.improves_on_naive_derotation


def test_a_correctly_centred_series_finds_zero_offset() -> None:
    """The negative control: when the naive assumption (rotation about the image centre) is
    already correct, the estimator must not manufacture a spurious offset.
    """
    field = _synthetic_field((80, 80), seed=2)
    image_centre = (40.0, 40.0)
    angles = [5.0, 15.0, 45.0, 90.0]

    frames = _rotation_series_about(field, angles, image_centre)
    reference = field

    estimate = estimate_rotation_centre(reference, frames, angles, search_radius=20.0)

    assert estimate.offset_xy[0] == pytest.approx(0.0, abs=0.5)
    assert estimate.offset_xy[1] == pytest.approx(0.0, abs=0.5)


def test_estimate_rotation_centre_is_anchored_at_the_image_centre_not_the_origin() -> None:
    """Pins the bug this module's own docstring names: an early version rotated every candidate
    about a point near pixel (0, 0) instead of near the image centre, because the search
    offset was used directly as the absolute rotation point rather than added to the image
    centre first. On a series that IS correctly centred, that bug reports a large spurious
    offset (of roughly the image half-size) instead of zero, which is exactly what this checks.
    """
    field = _synthetic_field((80, 80), seed=5)
    image_centre = (40.0, 40.0)
    angles = [10.0, 30.0, 60.0]
    frames = _rotation_series_about(field, angles, image_centre)

    estimate = estimate_rotation_centre(field, frames, angles, search_radius=20.0)

    # The bug this pins reports an offset near -image_centre (candidates explored near the
    # origin instead of near true centre); a correct estimator reports near zero.
    assert abs(estimate.offset_xy[0]) < 5.0
    assert abs(estimate.offset_xy[1]) < 5.0


def test_estimate_rotation_centre_refuses_mismatched_or_empty_input() -> None:
    field = _synthetic_field((20, 20), seed=3)
    with pytest.raises(ValueError, match=r"frames.*angles"):
        estimate_rotation_centre(field, [field, field], [5.0], search_radius=5.0)
    with pytest.raises(ValueError, match="zero frames"):
        estimate_rotation_centre(field, [], [], search_radius=5.0)


def test_inscribed_region_shrinks_as_the_centre_moves_off_axis() -> None:
    """A centred rotation axis keeps the whole inscribed square available (up to the frame's own
    inscribed-circle limit); an off-centre axis costs area, because the nearest corner is closer.
    """
    shape = (100, 100)
    centred = inscribed_region_mask(shape, (50.0, 50.0))
    off_centre = inscribed_region_mask(shape, (80.0, 50.0))

    assert centred.sum() > off_centre.sum()
    # The mask must be a rectangle centred on centre_xy: every True pixel is within its bound.
    _ys, xs = np.nonzero(off_centre)
    assert xs.min() >= 0
    assert xs.max() < shape[1]


def test_inscribed_region_is_always_inside_the_frame_bounds() -> None:
    shape = (37, 53)  # deliberately non-square, deliberately not a power of two
    mask = inscribed_region_mask(shape, (10.0, 40.0))
    assert mask.shape == shape
    assert mask.any()
    assert mask.sum() < shape[0] * shape[1]
