"""Join a labelled section to a rotation series, and refuse when that would be wrong.

This is the only sanctioned route from masks plus frames to a per-mineral anisotropy number.
That is a deliberate narrowing rather than convenience: the two failures this project has
actually suffered — a stage rotation silently inverting to zero anisotropy (N3), and an
anisotropy threshold that was secretly a brightness classifier (N2) — are both invisible at the
call site and both preventable at the boundary. Code that goes around this module gets neither
protection, which is exactly what happened to KHANYA's first attempt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from reefprint.acquire.series import RotationGeometry, RotationSeries
from reefprint.bridge.section import LabelledSection, LabelProvenance
from reefprint.polarim.stokes import MIN_ANGLES, stokes_from_rotation_series

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

__all__ = [
    "MIN_PIXELS_PER_MINERAL",
    "MineralStatistic",
    "SectionMeasurement",
    "group_by_locality",
    "measure_section",
]

#: Below this many labelled pixels a mineral is reported as absent rather than measured.
#: Declared threshold, not a physical constant: it is where the interquartile range of the
#: anisotropy distribution stops moving with n on the phantom. Rule 1 — an assumption, labelled.
MIN_PIXELS_PER_MINERAL = 500

#: Free parameters in the Stokes fit (S0, S1, S2). Used to de-bias the noise estimate read off
#: the residual: a p-parameter least-squares fit over n points leaves only (n - p) degrees of
#: freedom, so the raw residual RMS underestimates sigma by sqrt((n - p) / n).
_STOKES_PARAMETERS = 3


@dataclass(frozen=True, slots=True)
class MineralStatistic:
    """One mineral's anisotropy distribution, and the noise floor it is sitting on.

    The floor is not supplementary information. Finding N2 established that a perfectly
    isotropic phase does not read zero anisotropy — it reads roughly
    ``sigma * sqrt(8 / n) * sqrt(pi / 2) / S0``, which *rises as reflectance falls*. A bare
    median is therefore uninterpretable, and comparing two minerals' medians without their
    floors compares their brightness as much as their optics. Carrying the two together in one
    frozen record is the cheapest way to make that mistake unavailable.

    Attributes:
        mineral: Name from the section's codebook.
        n_pixels: Labelled pixels this was measured over. The honest n for any CI (Rule 4).
        anisotropy_median: Median DOLP. Median rather than mean because the distribution is
            bounded in [0, 1] and skewed by grain-boundary pixels where two phases share one
            detector element.
        anisotropy_p25: 25th percentile.
        anisotropy_p75: 75th percentile.
        s0_median: Median recovered S0, in the series' own intensity units.
        noise_floor_median: Median N2 floor over the same pixels, same units as the anisotropy.
    """

    mineral: str
    n_pixels: int
    anisotropy_median: float
    anisotropy_p25: float
    anisotropy_p75: float
    s0_median: float
    noise_floor_median: float

    @property
    def median_over_floor(self) -> float:
        """Median anisotropy in units of its own noise floor. The number worth comparing.

        Near 1.0 means "indistinguishable from isotropic at this reflectance and this n",
        whatever the raw median happens to be. This is the quantity that is comparable between a
        bright sulphide and dark gangue; the raw median is not.
        """
        return float(self.anisotropy_median / max(self.noise_floor_median, 1e-12))


@dataclass(frozen=True, slots=True)
class SectionMeasurement:
    """The result of measuring one section — including the result "not measured, because".

    A skipped section is data. The count of skips and their reasons is what distinguishes one
    corrupt mask from a systematically transposed dataset, and that distinction decides whether
    the fix is an hour or a rewrite. Returning it rather than raising is why a run over 47
    sections finishes and reports, instead of dying on the first bad one.

    Attributes:
        skipped: ``None`` if measured, otherwise the reason in one line.
        detail: Machine-readable specifics of a skip, e.g. the two disagreeing shapes.
    """

    section_id: str
    locality: str
    provenance: LabelProvenance
    geometry: RotationGeometry
    n_angles: int
    per_mineral: tuple[MineralStatistic, ...]
    n_pixels_measured: int
    n_pixels_unlabelled: int
    skipped: str | None = None
    detail: tuple[tuple[str, str], ...] = ()

    @property
    def was_measured(self) -> bool:
        return self.skipped is None

    def by_name(self) -> dict[str, MineralStatistic]:
        return {stat.mineral: stat for stat in self.per_mineral}


def _skip(
    section: LabelledSection,
    series: RotationSeries,
    reason: str,
    detail: tuple[tuple[str, str], ...] = (),
) -> SectionMeasurement:
    return SectionMeasurement(
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


def _noise_floor(residual_rms: np.ndarray, s0: np.ndarray, n_angles: int) -> np.ndarray:
    """Finding N2's floor, per pixel: the anisotropy a truly isotropic phase would read.

    ``sigma`` is estimated from the fit residual rather than declared, so the floor tracks the
    actual acquisition instead of an assumed detector. For a uniform angle set the Stokes
    covariance is ``sigma**2 * diag(4/n, 8/n, 8/n)``, so ``S1`` and ``S2`` each carry standard
    deviation ``sigma * sqrt(8/n)``; the magnitude of that two-component Gaussian has mean
    ``sqrt(pi/2)`` times its per-component sigma, and dividing by ``S0`` turns it into DOLP.
    """
    dof_correction = np.sqrt(n_angles / max(n_angles - _STOKES_PARAMETERS, 1))
    sigma = np.asarray(residual_rms, dtype=float) * dof_correction
    floor = sigma * np.sqrt(8.0 / n_angles) * np.sqrt(np.pi / 2.0)
    return np.divide(floor, s0, out=np.full_like(floor, np.inf), where=s0 > 0)


def measure_section(
    section: LabelledSection,
    series: RotationSeries,
    *,
    min_pixels: int = MIN_PIXELS_PER_MINERAL,
) -> SectionMeasurement:
    """Measure per-mineral anisotropy for one section, or say why it could not be.

    **The geometry check is unconditional and there is no argument that disables it.** That is
    the entire lesson of finding N3: the guard already existed on :class:`RotationSeries`, and
    the first real caller bypassed it by building the intensity array itself and calling the
    inversion directly. A guard that can be routed around is documentation. So it lives here, on
    the only path in.

    Note the asymmetry in how the two classes of failure are handled, which is not an
    inconsistency:

    * **Wrong geometry raises.** Which element rotated is a property of the acquisition
      protocol, constant across a dataset. If one section is a stage rotation they all are, and
      47 identical skip records inviting someone to pool the zero survivors is worse than one
      exception naming the cause.
    * **A shape or angle-count problem skips.** Those are per-section defects, and their *count*
      is the diagnosis — one bad mask against a transposed archive.

    Args:
        section: Labels, codebook, locality and provenance.
        series: Frames on the same pixel grid. Must be
            :data:`~reefprint.acquire.series.RotationGeometry.ANALYSER`.
        min_pixels: Minerals with fewer labelled pixels are omitted, not measured thinly.

    Returns:
        The measurement, with ``skipped`` set if nothing could be measured.

    Raises:
        ValueError: The series is a stage rotation or its geometry was never recorded. See
            :meth:`~reefprint.acquire.series.RotationSeries.require_analyser_rotation`.
    """
    series.require_analyser_rotation()

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

    stokes = stokes_from_rotation_series(series.frames, series.angles_rad)
    anisotropy = np.asarray(stokes.anisotropy)
    s0 = np.asarray(stokes.s0)
    floor = _noise_floor(np.asarray(stokes.residual_rms), s0, series.n_angles)

    stats: list[MineralStatistic] = []
    measured = 0
    for name in sorted(set(section.codebook.values())):
        mask = section.mineral_mask(name)
        count = int(mask.sum())
        if count < min_pixels:
            continue
        measured += count
        values = anisotropy[mask]
        stats.append(
            MineralStatistic(
                mineral=name,
                n_pixels=count,
                anisotropy_median=float(np.median(values)),
                anisotropy_p25=float(np.percentile(values, 25)),
                anisotropy_p75=float(np.percentile(values, 75)),
                s0_median=float(np.median(s0[mask])),
                noise_floor_median=float(np.median(floor[mask])),
            )
        )

    if not stats:
        return _skip(
            section,
            series,
            f"no mineral reached {min_pixels} labelled pixels",
            (("codebook_size", str(len(set(section.codebook.values())))),),
        )

    return SectionMeasurement(
        section_id=section.section_id,
        locality=section.locality,
        provenance=section.provenance,
        geometry=series.geometry,
        n_angles=series.n_angles,
        per_mineral=tuple(stats),
        n_pixels_measured=measured,
        n_pixels_unlabelled=section.n_unlabelled,
    )


def group_by_locality(
    measurements: Iterable[SectionMeasurement],
) -> dict[str, tuple[SectionMeasurement, ...]]:
    """Group measured sections by locality, refusing to mix label provenance.

    It groups and does not aggregate, on purpose. Pooling medians of medians across sections
    would produce a number with no defensible confidence interval, and Rule 4 requires every
    metric to carry one sized at honest n. The caller that knows what it is estimating can
    aggregate; this function's job is only to make sure the two things that must never be
    silently combined are not.

    Sections whose measurement was skipped are dropped here — they are still in the input list
    for anyone counting failures, which is the place that count belongs.

    Raises:
        ValueError: Ground-truth and predicted labels appear in the same input. Their average is
            neither a statement about minerals nor about the model. See :class:`LabelProvenance`.
    """
    measured = [m for m in measurements if m.was_measured]
    provenances = {m.provenance for m in measured}
    if len(provenances) > 1:
        names = ", ".join(sorted(p.name for p in provenances))
        msg = (
            f"cannot group {names} in one set: a statistic over predicted labels inherits the "
            f"segmenter's confusions, so its average with a ground-truth statistic describes "
            f"neither the minerals nor the model. Group them separately and compare."
        )
        raise ValueError(msg)

    grouped: dict[str, list[SectionMeasurement]] = {}
    for measurement in measured:
        grouped.setdefault(measurement.locality, []).append(measurement)
    return {locality: tuple(items) for locality, items in sorted(grouped.items())}


def held_out_localities(
    measurements: Sequence[SectionMeasurement],
) -> tuple[str, ...]:
    """The distinct localities present, sorted. The unit every split must be taken over.

    Exposed so a caller can assert on it rather than assume it: a set of measurements that turns
    out to span one locality cannot support a held-out-locality claim at all, and that is worth
    discovering before the metric is computed rather than in the talk.
    """
    return tuple(sorted({m.locality for m in measurements if m.was_measured}))
