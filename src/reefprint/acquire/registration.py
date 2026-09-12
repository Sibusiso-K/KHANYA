"""Per-frame registration for a rotation series whose rotation axis is not the image centre.

**The problem this exists for.** Session 17's registration finding: LumenStone S3 v2's frames
are not registered — a given pixel is a different physical point in every frame, because the
field rotates with the specimen about an axis that is off-image-centre and *varies by section*.
Naive centred de-rotation (rotate every frame about the image centre by its nominal filename
angle) does not fix this: it helped dramatically on one section and hurt another
(`WORKBOARD.md` §0 C1), which is exactly the signature of a wrong-centre correction — see the
module docstring's derivation below.

**Why this is solvable at all, and why nominal angles are the load-bearing fact.** Each frame's
angle relative to the reference frame is *known* from its filename (``r005`` = 5 degrees, and so
on) — the acquisition protocol records it even though the rotation axis's position is unknown.
That converts an otherwise underdetermined blind-registration problem (which would need to
recover both rotation and translation per frame pair, independently) into a much smaller one:
a single unknown 2-D point (the true rotation centre, one value for the whole series) that must
explain every frame's departure from a naive, centred de-rotation.

**The forward model.** A point ``p`` in the specimen's frame-0 orientation appears in frame ``i``
(rotated by the true angle ``theta_i`` about the true centre ``C``) at
``p_i = R(theta_i) @ (p - C) + C``. De-rotating frame ``i`` about the *wrong* centre ``C0``
(typically the image centre) by ``-theta_i`` produces an image that is frame 0, **translated** by
a vector that depends on ``theta_i`` and on ``C - C0`` — not a rotation error, a translation one.
That is exactly why naive de-rotation "worked" on one section and not another: the translation's
magnitude and direction both depend on the (unknown, per-section) offset ``C - C0``, so its
effect on any one frame pair looks like noise until the offset itself is known.

**The estimator.** Rather than derive the offset algebraically from measured per-frame
translations (a coordinate-convention-sensitive derivation that is easy to get subtly wrong — see
``docs/BUILDLOG.md`` for the two failed attempts this session made before switching approach),
:func:`estimate_rotation_centre` searches directly: for a candidate offset, de-rotate every frame
about the corresponding candidate centre by its own known nominal angle, and score the total
correlation against the reference frame. The score is maximised exactly at the true offset (the
correct centre is the only one where every frame's de-rotation is literally the reference frame),
so this is a plain 2-D optimisation, not a fit that could silently converge to a locally
plausible but wrong answer the way an under-constrained algebraic derivation can.
:func:`_coarse_to_fine_search` finds it by a grid search that refines around its own best
candidate — plain Nelder-Mead from a naive centred start was tried and got stuck in a shallow
region near zero offset on synthetic data with a known answer; the coarse grid does not have that
failure mode, and is simple enough to reason about correctness for directly.

**What this proves, and what it does not.** :mod:`tests.test_registration` validates this against
a *synthetic* off-centre rotation series with a known offset — the same leg-(a)-before-leg-(b)
discipline the rest of this project uses. It proves the estimator recovers a known answer. It
says nothing about whether the real S3 v2 archive's rotation centre is recoverable this way, how
much it varies section to section, or whether a corrected, cropped stack then clears
:func:`~reefprint.polarim.geometry.harmonic_signature`'s detection threshold — that is leg (b),
and it has not been run at the time this module was written (memory-constrained locally; the
real archive is 5.2 GB and a full section's frame stack needs roughly 5 GB once constructed,
per ``experiments/003-s3v2-extinction/run.py``'s own docstring — routed to Kaggle instead, see
``experiments/007-s3v2-registration/``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from skimage.transform import AffineTransform, warp

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = [
    "RegisteredFrame",
    "RotationCentreEstimate",
    "estimate_rotation_centre",
    "inscribed_region_mask",
    "rotate_about",
]


def rotate_about(frame: FloatArray, angle_deg: float, centre_xy: tuple[float, float]) -> FloatArray:
    """Rotate ``frame`` by ``angle_deg`` about ``centre_xy`` (an ``(x, y)`` pixel coordinate).

    Built directly on :class:`~skimage.transform.AffineTransform` rather than
    :func:`skimage.transform.rotate`'s own ``center`` argument, so the exact rotation-about-a-
    point algebra is visible and checkable in one place, rather than trusting a library default
    whose sign and axis convention would otherwise have to be verified empirically every time it
    is used (as this module's own development did, twice, incorrectly, before switching to
    building the transform explicitly).
    """
    theta = np.deg2rad(angle_deg)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    rotation = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
    centre = np.asarray(centre_xy, dtype=float)
    translation = centre - rotation @ centre
    matrix = np.array(
        [
            [rotation[0, 0], rotation[0, 1], translation[0]],
            [rotation[1, 0], rotation[1, 1], translation[1]],
            [0.0, 0.0, 1.0],
        ]
    )
    return warp(frame, AffineTransform(matrix=matrix).inverse, output_shape=frame.shape)


@dataclass(frozen=True, slots=True)
class RotationCentreEstimate:
    """The estimated rotation-centre offset from image centre, and how well it scored.

    :param offset_xy: ``(dx, dy)`` in pixels — the true rotation centre is the image centre plus
        this offset. Zero means the naive, centred de-rotation was already correct.
    :param score: total pairwise correlation against the reference frame at this offset. Higher
        is better; compare against :meth:`score_at_zero_offset` to judge whether registration
        found anything at all worth correcting.
    :param score_at_zero_offset: the same score evaluated at zero offset (i.e. what naive centred
        de-rotation already achieves) — reported alongside every estimate so an improvement can
        be judged rather than assumed. Rule 3's trivial-baseline discipline, applied to a
        registration search rather than a classifier.
    """

    offset_xy: tuple[float, float]
    score: float
    score_at_zero_offset: float

    @property
    def improves_on_naive_derotation(self) -> bool:
        return self.score > self.score_at_zero_offset


def estimate_rotation_centre(
    reference: FloatArray,
    frames: list[FloatArray],
    angles_deg: list[float],
    *,
    search_radius: float = 40.0,
    levels: int = 4,
    steps_per_level: int = 9,
) -> RotationCentreEstimate:
    """Find the ``(dx, dy)`` offset of the true rotation centre from the image centre.

    :param reference: the frame at angle 0 (or whatever angle the others' ``angles_deg`` are
        relative to). Every candidate offset is scored by how well it de-rotates ``frames`` back
        onto this one.
    :param frames: the other frames in the series, same shape as ``reference``.
    :param angles_deg: nominal rotation angle of each entry in ``frames``, relative to
        ``reference`` — read from the acquisition protocol (a filename, a logged stepper
        position), never estimated. This is what makes the search 2-D rather than
        one-rotation-and-one-translation-per-frame.
    :param search_radius: half-width, in pixels, of the coarsest grid's search window. Should
        comfortably bracket the largest offset plausible for the rig or archive in question —
        too small silently truncates the search, so this is a parameter to state and check
        against the section size, not a constant to leave untouched.
    :param levels: how many grid-then-refine passes to run. Each level narrows the window by
        ``steps_per_level / 2`` and centres it on the previous level's best candidate.
    :param steps_per_level: grid points per axis per level. Validated to sub-pixel accuracy at
        the default (4 levels, 9 steps) on synthetic data — see
        ``tests/test_registration.py::test_recovers_a_known_off_centre_rotation``.

    :raises ValueError: if ``frames`` and ``angles_deg`` disagree in length, or either is empty.
    """
    if len(frames) != len(angles_deg):
        raise ValueError(
            f"{len(frames)} frames but {len(angles_deg)} angles — one nominal angle per frame "
            "is required, since the angle is what makes this search tractable at all."
        )
    if len(frames) == 0:
        raise ValueError("cannot estimate a rotation centre from zero frames")

    # offset_xy is relative to the IMAGE centre, per this function's contract — every candidate
    # rotation point is that centre plus the offset, never the offset alone. Losing this "plus
    # image centre" step was the actual bug behind this module's first two failed validation
    # runs: it silently rotated every candidate about a point near pixel (0, 0) instead of near
    # the image centre, so the search explored the wrong region of the plane entirely while
    # still returning a plausible-looking number. Pinned by
    # ``test_estimate_rotation_centre_is_anchored_at_the_image_centre_not_the_origin``.
    image_centre = np.array([reference.shape[1] / 2.0, reference.shape[0] / 2.0])

    def total_correlation(offset_xy: FloatArray) -> float:
        candidate_centre = image_centre + offset_xy
        total = 0.0
        for angle, frame in zip(angles_deg, frames, strict=True):
            derotated = rotate_about(frame, -angle, tuple(candidate_centre))
            total += float(np.corrcoef(reference.ravel(), derotated.ravel())[0, 1])
        return total

    score_at_zero = total_correlation(np.array([0.0, 0.0]))
    best_offset = _coarse_to_fine_search(
        total_correlation,
        start=np.array([0.0, 0.0]),
        span=search_radius,
        steps=steps_per_level,
        levels=levels,
    )
    best_score = total_correlation(best_offset)
    return RotationCentreEstimate(
        offset_xy=(float(best_offset[0]), float(best_offset[1])),
        score=best_score,
        score_at_zero_offset=score_at_zero,
    )


def _coarse_to_fine_search(
    objective: Callable[[FloatArray], float],
    *,
    start: FloatArray,
    span: float,
    steps: int,
    levels: int,
) -> FloatArray:
    """Grid search, refined around its own best candidate, ``levels`` times.

    Not a general-purpose optimiser: it exists because a direct local method (Nelder-Mead from a
    naive start) got stuck near zero offset on a synthetic case with a known nonzero answer,
    while this coarse-to-fine grid found the true offset to sub-pixel accuracy on the same case.
    A grid is also trivially parallel per candidate, which matters once this runs against a real
    section instead of a small synthetic one.
    """
    best = start
    remaining_span = span
    for _ in range(levels):
        grid = np.linspace(-remaining_span, remaining_span, steps)
        best_score = -np.inf
        best_candidate = best
        for dx in grid:
            for dy in grid:
                candidate = best + np.array([dx, dy])
                score = objective(candidate)
                # A candidate that rotates content entirely outside the frame can score NaN
                # (zero-variance padding makes correlation undefined) — never let that win, and
                # never let it poison the running best the way `NaN > x` silently would (`NaN`
                # compares False against everything, so a NaN seed as the first "best" could
                # never be replaced by a real, better score).
                if np.isnan(score):
                    continue
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
        best = best_candidate
        remaining_span /= steps / 2.0
    return best


@dataclass(frozen=True, slots=True)
class RegisteredFrame:
    """One frame, de-rotated about the estimated true centre, plus the crop every frame shares.

    :param image: the de-rotated frame, still at the original resolution — cropping to
        :attr:`valid_bounds` is a separate step (:func:`inscribed_region_mask` computes the
        shared region; the caller slices with it), so a mask can be transformed through the same
        rotation before either is cropped.
    """

    image: FloatArray
    angle_deg: float


def inscribed_region_mask(
    shape: tuple[int, int], centre_xy: tuple[float, float]
) -> npt.NDArray[np.bool_]:
    """The region of ``shape`` guaranteed to stay inside the frame at every rotation angle,
    rotated about ``centre_xy``.

    Conservative and closed-form rather than measured per frame: the largest axis-aligned
    square inscribed in the circle of radius ``r = min(distance from centre_xy to the four
    corners)`` is inside the frame at *every* rotation angle, because a full rotation sweeps that
    circle onto itself. Always uses the full 0-360 degree circle, deliberately not parametrised
    on a narrower angle range — this project's series can span the full range (S3 v2 uses up to
    360 degrees), and a range-aware, less conservative crop would need its own separate
    derivation and test that nothing currently needs.
    """
    height, width = shape
    cx, cy = centre_xy
    corners = np.array([[0, 0], [width, 0], [0, height], [width, height]])
    radius = float(np.min(np.linalg.norm(corners - np.array([cx, cy]), axis=1)))
    # Half the side of the largest square inscribed in a circle of this radius, centred at
    # (cx, cy): side = radius * sqrt(2).
    half_side = radius / np.sqrt(2.0)
    y_grid, x_grid = np.ogrid[:height, :width]
    return (np.abs(x_grid - cx) <= half_side) & (np.abs(y_grid - cy) <= half_side)
