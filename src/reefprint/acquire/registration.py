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

**A real failure mode, found on real data, not fully understood yet.** Leg (b), once run
(``experiments/007-s3v2-registration/``), found a plausible-looking but wrong offset on one real
section (``S3_test_03``): a large offset, a positive but modest score improvement, and — checked
by eye (``experiments/009-s3test03-visual-check/``) — no visible change in a tracked grain's
position between the naive and "corrected" de-rotations. :func:`estimate_rotation_centre`'s
``roi_mask`` parameter was added to exclude border and background content from the objective, on
the hypothesis that such content — which does not rotate the way the specimen interior does —
was winning the correlation search instead of the specimen. **The mask did not fix it**
(``experiments/010-s3test03-masked-rerun/``): masked scoring found an even larger, still-wrong-
looking offset. Worse, investigating that led to a bigger problem: **the unmasked search itself
is not reproducible run to run on this real section, with unchanged code and unchanged input** —
one run finds an offset four times larger than another. The naive-condition pipeline (which
never touches this search) reproduces bit-for-bit across the same two runs, ruling out a data or
decode difference. The leading hypothesis is that real mineral texture's self-similarity gives
the correlation objective multiple near-tied local optima, and ``_coarse_to_fine_search``'s
``if score > best_score`` comparison has no tie-break rule for when floating-point noise decides
between them (CLAUDE.md Rule 5: sort every traversal, tie-break every min/max — this does
neither). **Until that is fixed and checked, no specific offset this function returns on real
data should be trusted to the precision it is reported at**, on `S3_test_03` or any other
section — see ``experiments/010-s3test03-masked-rerun/README.md`` for the full account and what
would need to happen before this is resolved. The ``roi_mask`` feature itself remains correct
and tested on controlled synthetic data
(``test_roi_mask_excludes_a_non_rotating_corrupted_region_and_sharpens_discrimination``); it did
not turn out to be the fix this particular real-data problem needed.

**A second, published estimator, added per CLAUDE.md Rule 10.** Korshunov et al. 2025 (the
LumenStone dataset authors; doi:10.17073/2500-0632-2025-05-416) register their XPL/PPL image
pairs by SIFT keypoint matching followed by a RANSAC-fitted affine transform.
:func:`estimate_rotation_centre_sift_ransac` is that method, adapted to this problem: fit an
independent rigid (rotation + translation) transform per frame from SIFT-matched keypoints,
recover each frame's implied rotation centre algebraically (the fixed point of the fitted
rotation), and combine across frames with the median. Unlike the grid search above, this method
is **diagnosable per frame** — inlier count, match count and residual RMS say *why* a frame's
estimate should or should not be trusted, rather than only returning a number — and it is
deterministic by construction: SIFT itself has no randomness, and :func:`skimage.measure.ransac`
is seeded (``rng=``) rather than left to draw from unseeded global state, which is exactly what
the grid search above lacks (no tie-break rule) and what made it non-reproducible on real data.
A method that cannot pass the determinism test (:mod:`tests.test_registration`) does not get a
verdict, whichever estimator it is — this one is not assumed better, only tried, per Rule 10.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from skimage.feature import SIFT, match_descriptors
from skimage.measure import ransac
from skimage.transform import AffineTransform, EuclideanTransform, warp

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = [
    "RegisteredFrame",
    "RotationCentreEstimate",
    "SiftRansacCentreEstimate",
    "SiftRansacFrameEstimate",
    "estimate_rotation_centre",
    "estimate_rotation_centre_sift_ransac",
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
    roi_mask: npt.NDArray[np.bool_] | None = None,
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
    :param roi_mask: boolean array, same shape as ``reference``, restricting which pixels the
        correlation objective scores. ``None`` (the default) scores the whole frame. **Exclude
        background, resin, and border content here** — it does not rotate the way the specimen
        interior does, and an unmasked search can be won by aligning it instead of the specimen,
        which is exactly the failure found on real data (``S3_test_03``, module docstring) and
        pinned by
        ``test_roi_mask_excludes_a_non_rotating_corrupted_region_and_sharpens_discrimination``.
        Defined once, in the reference frame's coordinates, and applied unchanged to every
        candidate — a mask that moved with the candidate could be gamed by the search the same
        way the unmasked objective already was.

    :raises ValueError: if ``frames`` and ``angles_deg`` disagree in length, either is empty, or
        ``roi_mask`` selects no pixels at all.
    """
    if len(frames) != len(angles_deg):
        raise ValueError(
            f"{len(frames)} frames but {len(angles_deg)} angles — one nominal angle per frame "
            "is required, since the angle is what makes this search tractable at all."
        )
    if len(frames) == 0:
        raise ValueError("cannot estimate a rotation centre from zero frames")
    if roi_mask is not None and not roi_mask.any():
        raise ValueError("roi_mask selects no pixels — nothing left for the objective to score")

    # offset_xy is relative to the IMAGE centre, per this function's contract — every candidate
    # rotation point is that centre plus the offset, never the offset alone. Losing this "plus
    # image centre" step was the actual bug behind this module's first two failed validation
    # runs: it silently rotated every candidate about a point near pixel (0, 0) instead of near
    # the image centre, so the search explored the wrong region of the plane entirely while
    # still returning a plausible-looking number. Pinned by
    # ``test_estimate_rotation_centre_is_anchored_at_the_image_centre_not_the_origin``.
    image_centre = np.array([reference.shape[1] / 2.0, reference.shape[0] / 2.0])
    reference_scored = reference if roi_mask is None else reference[roi_mask]

    def total_correlation(offset_xy: FloatArray) -> float:
        candidate_centre = image_centre + offset_xy
        total = 0.0
        for angle, frame in zip(angles_deg, frames, strict=True):
            derotated = rotate_about(frame, -angle, tuple(candidate_centre))
            derotated_scored = derotated if roi_mask is None else derotated[roi_mask]
            total += float(np.corrcoef(reference_scored.ravel(), derotated_scored.ravel())[0, 1])
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


@dataclass(frozen=True, slots=True)
class SiftRansacFrameEstimate:
    """One frame's independent rotation-centre estimate from SIFT-matched keypoints + RANSAC.

    :param angle_deg: the frame's nominal angle, read from acquisition metadata — recorded here
        only for comparison against :attr:`fitted_angle_deg`, never used to constrain the fit.
    :param fitted_angle_deg: the rotation RANSAC actually recovered from the matched keypoints,
        independent of the nominal angle. A large disagreement with ``angle_deg`` is itself a
        diagnostic the grid-search estimator has no equivalent of.
    :param centre_xy: the true rotation centre implied by this frame's fitted transform, or
        ``None`` if too few matches or inliers survived, or the fitted rotation was too close to
        zero for the centre to be numerically recoverable (a near-identity rotation's fixed point
        is ill-conditioned — see the module docstring's ``(I - R) c = t`` derivation).
    :param inlier_count: RANSAC inliers. Low relative to :attr:`match_count` means the fitted
        transform is trusted by few of its own candidate matches.
    :param match_count: SIFT matches before RANSAC. Low in absolute terms means the frame had
        little matchable texture against the reference at all.
    :param residual_rms: RMS reprojection error of the inlier matches under the fitted transform,
        in pixels. High alongside a high inlier count means the fit is systematically loose, not
        merely short of data.
    """

    angle_deg: float
    fitted_angle_deg: float
    centre_xy: tuple[float, float] | None
    inlier_count: int
    match_count: int
    residual_rms: float


@dataclass(frozen=True, slots=True)
class SiftRansacCentreEstimate:
    """Rotation-centre offset from image centre, estimated by SIFT + RANSAC per frame and
    combined by median across frames that produced a usable estimate.

    :param offset_xy: ``(dx, dy)`` in pixels, same contract as
        :attr:`RotationCentreEstimate.offset_xy` — the true rotation centre is the image centre
        plus this offset. ``None`` if no frame produced a usable estimate.
    :param per_frame: one :class:`SiftRansacFrameEstimate` per input frame, in input order —
        the diagnostic this method exists to provide, unlike the grid search's single number.
    """

    offset_xy: tuple[float, float] | None
    per_frame: tuple[SiftRansacFrameEstimate, ...]

    @property
    def usable_frame_count(self) -> int:
        return sum(1 for frame in self.per_frame if frame.centre_xy is not None)


def _rotation_centre_from_euclidean_transform(
    transform: EuclideanTransform,
) -> tuple[float, float] | None:
    """Solve for the fixed point of a fitted rigid transform: ``c = R @ c + t`` rearranges to
    ``(I - R) @ c = t``. Near a zero rotation, ``I - R`` is near-singular — a pure translation has
    no well-defined centre at all — so this returns ``None`` rather than a numerically unstable
    answer, exactly the discipline the coarse-to-fine search's ``NaN`` guard applies for the same
    reason (module docstring, and CLAUDE.md Rule 5: no field should report a number the arithmetic
    behind it cannot support).
    """
    rotation = np.array(
        [
            [np.cos(transform.rotation), -np.sin(transform.rotation)],
            [np.sin(transform.rotation), np.cos(transform.rotation)],
        ]
    )
    identity_minus_rotation = np.eye(2) - rotation
    if abs(np.linalg.det(identity_minus_rotation)) < 1e-9:
        return None
    centre = np.linalg.solve(identity_minus_rotation, np.asarray(transform.translation))
    return (float(centre[0]), float(centre[1]))


def estimate_rotation_centre_sift_ransac(
    reference: FloatArray,
    frames: list[FloatArray],
    angles_deg: list[float],
    *,
    min_matches: int = 8,
    residual_threshold: float = 3.0,
    max_trials: int = 2000,
    rng: int = 0,
) -> SiftRansacCentreEstimate:
    """Find the ``(dx, dy)`` offset of the true rotation centre from the image centre, by SIFT
    keypoint matching and RANSAC — the method Korshunov et al. 2025 publish for XPL/PPL
    registration on this same dataset family (module docstring). See CLAUDE.md Rule 10.

    :param reference: the frame at angle 0 (or whatever angle the others' ``angles_deg`` are
        relative to). SIFT keypoints are detected here once and matched against every frame.
    :param frames: the other frames in the series, same shape as ``reference``.
    :param angles_deg: nominal angle of each entry in ``frames``, relative to ``reference`` —
        used only as a diagnostic comparison against the independently fitted
        :attr:`SiftRansacFrameEstimate.fitted_angle_deg`, never to constrain the fit. Unlike
        :func:`estimate_rotation_centre`, this method does not need the angle to be tractable —
        knowing it only sharpens the diagnostic.
    :param min_matches: fewest SIFT matches (and RANSAC inliers) required to trust a frame's
        transform. Below this, the frame contributes ``centre_xy=None`` rather than a fit RANSAC
        found from too little evidence to mean anything.
    :param residual_threshold: RANSAC's own inlier/outlier cutoff, in pixels of reprojection
        error under a candidate transform.
    :param max_trials: RANSAC's own trial cap. `skimage.measure.ransac`'s early-stopping
        (``stop_probability``) is left at its default, so the search is not artificially
        truncated for a genuinely hard frame.
    :param rng: seed passed straight to :func:`skimage.measure.ransac`'s own ``rng`` argument.
        SIFT itself draws no randomness; RANSAC's sample selection does, and leaving it unseeded
        is exactly the kind of missing tie-break the grid-search estimator's non-reproducibility
        finding (module docstring) turned out to hinge on. Fixed by default so two calls with
        identical input are bit-for-bit identical — the determinism test this module requires of
        either estimator before any offset from it is quoted.

    :raises ValueError: if ``frames`` and ``angles_deg`` disagree in length, or ``frames`` is
        empty — the same contract as :func:`estimate_rotation_centre`.
    """
    if len(frames) != len(angles_deg):
        raise ValueError(
            f"{len(frames)} frames but {len(angles_deg)} angles — one nominal angle per frame "
            "is required for the diagnostic comparison, even though the fit itself does not "
            "need it."
        )
    if len(frames) == 0:
        raise ValueError("cannot estimate a rotation centre from zero frames")

    reference_sift = SIFT()
    reference_sift.detect_and_extract(np.asarray(reference, dtype=np.float64))
    # SIFT reports keypoints as (row, col); this module's (x, y) convention throughout is
    # (col, row) — image_centre above is built from (width, height), i.e. (x, y). Flipping here,
    # once, is cheaper and less error-prone than carrying the wrong axis order through the fit.
    reference_keypoints_xy = reference_sift.keypoints[:, ::-1]

    per_frame: list[SiftRansacFrameEstimate] = []
    centres: list[tuple[float, float]] = []
    for angle, frame in zip(angles_deg, frames, strict=True):
        frame_sift = SIFT()
        frame_sift.detect_and_extract(np.asarray(frame, dtype=np.float64))
        frame_keypoints_xy = frame_sift.keypoints[:, ::-1]

        if len(reference_keypoints_xy) < 2 or len(frame_keypoints_xy) < 2:
            per_frame.append(SiftRansacFrameEstimate(angle, float("nan"), None, 0, 0, float("nan")))
            continue

        matches = match_descriptors(
            reference_sift.descriptors, frame_sift.descriptors, cross_check=True
        )
        if len(matches) < min_matches:
            per_frame.append(
                SiftRansacFrameEstimate(angle, float("nan"), None, 0, len(matches), float("nan"))
            )
            continue

        src = reference_keypoints_xy[matches[:, 0]]
        dst = frame_keypoints_xy[matches[:, 1]]
        transform, inliers = ransac(
            (src, dst),
            EuclideanTransform,
            min_samples=2,
            residual_threshold=residual_threshold,
            max_trials=max_trials,
            rng=rng,
        )
        if transform is None or inliers is None or inliers.sum() < min_matches:
            inlier_count = 0 if inliers is None else int(inliers.sum())
            per_frame.append(
                SiftRansacFrameEstimate(
                    angle, float("nan"), None, inlier_count, len(matches), float("nan")
                )
            )
            continue

        residual_rms = float(np.sqrt(np.mean(transform.residuals(src[inliers], dst[inliers]) ** 2)))
        centre_xy = _rotation_centre_from_euclidean_transform(transform)
        fitted_angle_deg = float(np.degrees(transform.rotation))
        per_frame.append(
            SiftRansacFrameEstimate(
                angle, fitted_angle_deg, centre_xy, int(inliers.sum()), len(matches), residual_rms
            )
        )
        if centre_xy is not None:
            centres.append(centre_xy)

    if not centres:
        return SiftRansacCentreEstimate(offset_xy=None, per_frame=tuple(per_frame))

    image_centre = np.array([reference.shape[1] / 2.0, reference.shape[0] / 2.0])
    median_centre = np.median(np.asarray(centres), axis=0)
    offset = median_centre - image_centre
    return SiftRansacCentreEstimate(
        offset_xy=(float(offset[0]), float(offset[1])), per_frame=tuple(per_frame)
    )
