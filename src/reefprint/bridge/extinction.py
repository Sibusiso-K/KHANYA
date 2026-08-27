"""Join a labelled section to a *stage* rotation series — leg (b)'s fallback route.

The mirror image of :mod:`reefprint.bridge.measure`. That module is the only sanctioned route
from an **analyser** series to per-mineral anisotropy, and it refuses a stage series
unconditionally (finding N3). This module is the only sanctioned route from a **stage** series to
per-mineral extinction, and it refuses an analyser series just as unconditionally — feeding a
rotating-analyser series to the fourth-harmonic fit would silently discard the second-harmonic
signal that series actually carries, the same class of wrong-tool mistake in the other direction.

**What this recovers is not the same quantity `measure_section` recovers**, and the two must not
be compared as if they were. ``measure_section`` reports DOLP, a *contrast* — bounded in [0, 1]
and comparable between minerals of different brightness. This module reports
:attr:`~reefprint.polarim.extinction.ExtinctionImage.extinction_depth`, which is **not**
contrast-normalised: crossed polars block the unpolarised pedestal, so there is no ``S0`` in a
stage series and no way to divide it out (see ``polarim/extinction.py``'s module docstring).
Comparing raw extinction depth between two minerals compares their bireflectance *and* their
brightness at once — finding N2 in a new costume. A wide difference in raw depth between a bright
sulphide and a dim one is not, by itself, evidence of a bireflectance difference.

Use it for what it is licensed for: telling a mineral that stays *exactly* dark (extinction depth
identically zero, cubic symmetry, not approximately) from one that extincts at all. That claim
does not need contrast normalisation, because zero is zero regardless of brightness. It cannot,
on its own, rank two extincting minerals against each other.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reefprint.acquire.series import RotationGeometry, RotationSeries
from reefprint.bridge.section import LabelledSection, LabelProvenance
from reefprint.polarim.extinction import MIN_ANGLES, extinction_from_stage_series

__all__ = [
    "MIN_PIXELS_PER_MINERAL",
    "MineralExtinctionStatistic",
    "SectionExtinctionMeasurement",
    "measure_section_extinction",
]

#: Same threshold as ``bridge.measure.MIN_PIXELS_PER_MINERAL``, and for the same declared
#: reason (Rule 1) — kept as a separate constant rather than a shared import so the two
#: modules can diverge later without one silently dragging the other.
MIN_PIXELS_PER_MINERAL = 500


@dataclass(frozen=True, slots=True)
class MineralExtinctionStatistic:
    """One mineral's raw extinction-depth distribution under a stage rotation.

    **Not comparable in brightness-normalised terms to another mineral's** — see the module
    docstring. What *is* licensed: asking whether a mineral is indistinguishable from zero.

    Attributes:
        mineral: Name from the section's codebook.
        n_pixels: Labelled pixels this was measured over. The honest n for any CI (Rule 4).
        extinction_depth_median: Median raw extinction depth, in the series' own intensity
            units squared. Zero for an exactly cubic phase; the module docstring explains why
            this is the one claim raw depth is licensed to make.
        extinction_depth_p25: 25th percentile.
        extinction_depth_p75: 75th percentile.
        crossing_ratio_median: Median ``dc / amplitude`` over the mineral's pixels. Pinned at
            1.0 for ideal crossed polars; the self-test the geometry carries for free (see
            :attr:`~reefprint.polarim.extinction.ExtinctionImage.crossing_ratio`).
    """

    mineral: str
    n_pixels: int
    extinction_depth_median: float
    extinction_depth_p25: float
    extinction_depth_p75: float
    crossing_ratio_median: float


@dataclass(frozen=True, slots=True)
class SectionExtinctionMeasurement:
    """The result of measuring one section under the extinction estimator, skip included.

    Mirrors :class:`~reefprint.bridge.measure.SectionMeasurement`. See that class for why a
    skip is data rather than an exception.
    """

    section_id: str
    locality: str
    provenance: LabelProvenance
    geometry: RotationGeometry
    n_angles: int
    per_mineral: tuple[MineralExtinctionStatistic, ...]
    n_pixels_measured: int
    n_pixels_unlabelled: int
    skipped: str | None = None
    detail: tuple[tuple[str, str], ...] = ()

    @property
    def was_measured(self) -> bool:
        return self.skipped is None

    def by_name(self) -> dict[str, MineralExtinctionStatistic]:
        return {stat.mineral: stat for stat in self.per_mineral}


def _skip(
    section: LabelledSection,
    series: RotationSeries,
    reason: str,
    detail: tuple[tuple[str, str], ...] = (),
) -> SectionExtinctionMeasurement:
    return SectionExtinctionMeasurement(
        section_id=section.section_id,
        locality=section.locality,
        provenance=section.provenance,
        geometry=series.geometry,
        n_angles=series.n_angles,
        per_mineral=(),
        n_pixels_measured=0,
        n_pixels_unlabelled=section.n_unlabelled,
        skipped=reason,
        detail=detail,
    )


def measure_section_extinction(
    section: LabelledSection,
    series: RotationSeries,
    *,
    min_pixels: int = MIN_PIXELS_PER_MINERAL,
) -> SectionExtinctionMeasurement:
    """Measure per-mineral extinction depth for one section, or say why it could not be.

    **The geometry check is unconditional, the mirror of ``measure_section``'s.** An analyser
    series fed here would have its second-harmonic content thrown away by a fourth-harmonic fit
    without complaint — a different silent wrong answer from N3's, not a safer one.

    Args:
        section: Labels, codebook, locality and provenance.
        series: Frames on the same pixel grid. Must be
            :data:`~reefprint.acquire.series.RotationGeometry.SPECIMEN`.
        min_pixels: Minerals with fewer labelled pixels are omitted, not measured thinly.

    Returns:
        The measurement, with ``skipped`` set if nothing could be measured.

    Raises:
        ValueError: The series is an analyser rotation or its geometry was never recorded. See
            :meth:`~reefprint.acquire.series.RotationSeries.require_specimen_rotation`.
    """
    series.require_specimen_rotation()

    if series.shape != section.shape:
        return _skip(
            section,
            series,
            "mask/frame shape mismatch",
            (("mask_shape", str(section.shape)), ("frame_shape", str(series.shape))),
        )
    if series.n_angles < MIN_ANGLES:
        return _skip(
            section,
            series,
            f"only {series.n_angles} angles, need {MIN_ANGLES}",
            (("n_angles", str(series.n_angles)),),
        )

    extinction = extinction_from_stage_series(series.frames, series.angles_rad)
    depth = np.asarray(extinction.extinction_depth)
    crossing_ratio = np.asarray(extinction.crossing_ratio)

    stats: list[MineralExtinctionStatistic] = []
    measured = 0
    for name in sorted(set(section.codebook.values())):
        mask = section.mineral_mask(name)
        count = int(mask.sum())
        if count < min_pixels:
            continue
        measured += count
        values = depth[mask]
        stats.append(
            MineralExtinctionStatistic(
                mineral=name,
                n_pixels=count,
                extinction_depth_median=float(np.median(values)),
                extinction_depth_p25=float(np.percentile(values, 25)),
                extinction_depth_p75=float(np.percentile(values, 75)),
                crossing_ratio_median=float(np.median(crossing_ratio[mask])),
            )
        )

    if not stats:
        return _skip(
            section,
            series,
            f"no mineral reached {min_pixels} labelled pixels",
            (("codebook_size", str(len(set(section.codebook.values())))),),
        )

    return SectionExtinctionMeasurement(
        section_id=section.section_id,
        locality=section.locality,
        provenance=section.provenance,
        geometry=series.geometry,
        n_angles=series.n_angles,
        per_mineral=tuple(stats),
        n_pixels_measured=measured,
        n_pixels_unlabelled=section.n_unlabelled,
    )
