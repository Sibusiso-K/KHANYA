"""Which element rotated? Decide it from the frames, not from the filename.

:class:`~reefprint.acquire.series.RotationGeometry` says why this matters and what it costs to
get wrong: a crossed-polars *stage* rotation modulates at ``4 phi`` while the Stokes inversion
fits ``2 theta``, the projection of one onto the other is zero, and every anisotropic mineral
comes back isotropic with no error raised. ``require_analyser_rotation`` refuses to guess. This
module is how the guess is replaced by a measurement.

The two geometries are separated by *which harmonic carries the modulation*:

===================================  =============================  =================
Geometry                             Model                          Modulation
===================================  =============================  =================
rotating analyser                    ``(S0 + S1 c2 + S2 s2) / 2``   2nd harmonic
rotating stage, fixed crossed polars ``|r1-r2|**2 (1 - c4) / 8``    4th harmonic
===================================  =============================  =================

So fit *both* at once,

    ``I(a) = A0 + A2c cos 2a + A2s sin 2a + A4c cos 4a + A4s sin 4a``

and ask which of ``|A2|`` and ``|A4|`` is real. Fitting them jointly rather than one after the
other matters whenever the angle set is not uniform: on an even grid the two harmonics are
orthogonal and it makes no difference, but on a set with gaps — a series with dropped frames,
or hand-stepped angles — power leaks between them, and a sequential fit attributes the leak to
whichever harmonic it tried first.

**"Which is real" is a noise question, so it is answered with the noise.** No fixed amplitude
threshold appears here; finding N2 is exactly the lesson that a fixed threshold on a modulation
depth is a brightness classifier in disguise. Instead the covariance of the fitted coefficients
is read straight off the design matrix, ``cov = sigma**2 (A.T A)**-1``, with ``sigma`` estimated
from the residuals of the joint fit. That gives each harmonic its own amplitude floor — the
amplitude it would show if it were pure noise — and the verdict compares against that floor.
It is exact for any angle set, uniform or not, and it needs no assumption that the noise is the
same in two different files.

One judgement call is declared rather than hidden: :data:`DETECTION_SNR`, how far above its own
noise floor a harmonic must sit before it counts as present. That is a decision threshold, not a
physical constant, and it is a keyword argument everywhere it is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

import numpy as np

from reefprint.acquire.series import RotationGeometry

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = [
    "DETECTION_SNR",
    "MIN_ANGLES_FOR_GEOMETRY",
    "HarmonicSignature",
    "HarmonicVerdict",
    "harmonic_signature",
]

#: Five free parameters (DC, two 2nd-harmonic, two 4th-harmonic), so five distinct angles.
#: In practice a published series has 36 or 72; this is the floor below which the question
#: cannot be asked at all, not a recommendation.
MIN_ANGLES_FOR_GEOMETRY = 5

#: Above this, the angle set cannot separate the two harmonics and no verdict is possible.
#: Matches ``stokes.MAX_DESIGN_CONDITION`` in spirit: refuse the inversion rather than return a
#: number that looks fine. A uniform grid over the full turn gives cond(A) close to 1.
MAX_DESIGN_CONDITION = 1.0e3

#: How far above its own noise floor a harmonic amplitude must sit to count as present.
#: A *declared decision threshold*, not a measured constant. At 5 the false-positive rate on
#: pure Gaussian noise is well under 1% per pixel, which matters because the verdict is taken
#: over many pixels at once.
DETECTION_SNR = 5.0

#: Geometry is a property of the acquisition, so it is decided on the pixels that actually
#: modulate. Dark resin and isotropic grains carry no information about which element turned;
#: including them only dilutes the evidence. Top decile by fitted modulation amplitude.
MODULATING_FRACTION = 0.10


class HarmonicVerdict(StrEnum):
    """What the harmonic content says about the acquisition geometry."""

    SECOND = "2nd harmonic only — consistent with a rotating analyser"
    FOURTH = "4th harmonic only — consistent with a stage rotation under crossed polars"
    BOTH = "both harmonics present — geometry is mixed, impure, or mislabelled"
    NEITHER = "no modulation above the noise floor — nothing anisotropic in view"

    def to_geometry(self) -> RotationGeometry:
        """Map the verdict onto a :class:`RotationGeometry`, refusing to over-claim.

        Only :data:`SECOND` and :data:`FOURTH` name a geometry. :data:`BOTH` and
        :data:`NEITHER` both return :data:`RotationGeometry.UNKNOWN`, because "I cannot tell"
        and "it is the convenient one" must not be the same value. Rule 1.
        """
        if self is HarmonicVerdict.SECOND:
            return RotationGeometry.ANALYSER
        if self is HarmonicVerdict.FOURTH:
            return RotationGeometry.SPECIMEN
        return RotationGeometry.UNKNOWN


@dataclass(frozen=True, slots=True)
class HarmonicSignature:
    """Second- and fourth-harmonic content of a rotation series, with the noise it sits on.

    Attributes:
        amplitude_2: ``sqrt(A2c**2 + A2s**2)`` per pixel — the rotating-analyser modulation.
        amplitude_4: ``sqrt(A4c**2 + A4s**2)`` per pixel — the crossed-polars stage modulation.
        floor_2: Amplitude the 2nd harmonic would show at this noise level if it were absent.
        floor_4: The same for the 4th harmonic.
        dc: Fitted constant term. Not ``S0``; the two agree only under the analyser model.
        n_angles: How many frames the fit used.
        verdict: The aggregate answer over the modulating pixels.
        snr_2: Aggregate ``amplitude_2 / floor_2`` over the modulating pixels.
        snr_4: The same for the 4th harmonic.
        detection_snr: The threshold the verdict used, recorded so a result can be re-read.

    ``snr_2`` and ``snr_4`` are the numbers to quote. They are dimensionless, they do not depend
    on the intensity units, and they are the evidence behind ``verdict`` rather than a summary
    of it.
    """

    amplitude_2: FloatArray
    amplitude_4: FloatArray
    floor_2: FloatArray
    floor_4: FloatArray
    dc: FloatArray
    n_angles: int
    verdict: HarmonicVerdict
    snr_2: float
    snr_4: float
    detection_snr: float

    @property
    def geometry(self) -> RotationGeometry:
        """The geometry this signature supports, or ``UNKNOWN`` when it supports neither."""
        return self.verdict.to_geometry()

    def explain(self) -> str:
        """One paragraph a human can check, for the build log and for the talk.

        Deliberately states the losing harmonic too. A verdict that only reports the winner
        cannot be distinguished from a verdict that never looked.
        """
        return (
            f"{self.n_angles} frames. 2nd harmonic at {self.snr_2:.1f}x its noise floor, "
            f"4th harmonic at {self.snr_4:.1f}x, threshold {self.detection_snr:.1f}x. "
            f"Verdict: {self.verdict.value}. Geometry: {self.geometry.name}."
        )


def _design(angles_rad: FloatArray) -> FloatArray:
    """``[1, cos2a, sin2a, cos4a, sin4a]`` — the joint two-harmonic model."""
    two = 2.0 * angles_rad
    four = 4.0 * angles_rad
    return np.stack(
        [
            np.ones_like(angles_rad),
            np.cos(two),
            np.sin(two),
            np.cos(four),
            np.sin(four),
        ],
        axis=1,
    )


def harmonic_signature(
    frames: FloatArray,
    angles_rad: FloatArray,
    *,
    detection_snr: float = DETECTION_SNR,
    modulating_fraction: float = MODULATING_FRACTION,
) -> HarmonicSignature:
    """Measure which harmonic carries the modulation, and so which element rotated.

    Args:
        frames: ``(n_angles, ...)``. Trailing axes are the pixel grid and are preserved; a
            flat ``(n_angles, n_pixels)`` sample from a large section works as well as a full
            image, which is what makes this affordable on a 5 GB archive.
        angles_rad: ``(n_angles,)``, the angle of whichever element moved. The verdict does not
            depend on knowing which one — that is the entire point.
        detection_snr: How far above its noise floor a harmonic must sit to count as present.
            A declared decision threshold; see :data:`DETECTION_SNR`.
        modulating_fraction: Fraction of pixels, ranked by modulation amplitude, that the
            aggregate verdict is taken over. Isotropic and unlit pixels say nothing about
            geometry.

    Returns:
        A :class:`HarmonicSignature`. Read ``verdict``, quote ``snr_2`` and ``snr_4``.

    Raises:
        ValueError: Fewer than :data:`MIN_ANGLES_FOR_GEOMETRY` angles; or the angle set cannot
            separate the two harmonics, judged on the design matrix condition number.

    A worked expectation, so a wrong answer is recognisable as wrong: on a series where the
    analyser turned, ``snr_4`` sits near 1 — its measured amplitude *is* its noise floor — while
    ``snr_2`` runs to tens or hundreds. On a stage rotation the two swap. Both large means the
    frames are not a clean example of either geometry, and that is a finding about the data, not
    a failure of this function.
    """
    frames = np.asarray(frames, dtype=float)
    angles = np.asarray(angles_rad, dtype=float)
    if angles.ndim != 1 or angles.size != frames.shape[0]:
        msg = f"angles_rad {angles.shape} does not match frames {frames.shape}"
        raise ValueError(msg)
    n_angles = angles.size
    if n_angles < MIN_ANGLES_FOR_GEOMETRY:
        msg = (
            f"{n_angles} angles cannot separate a 2nd harmonic from a 4th: the joint model has "
            f"{MIN_ANGLES_FOR_GEOMETRY} free parameters. A series this short can be inverted "
            f"for Stokes parameters but its geometry must come from the acquisition record."
        )
        raise ValueError(msg)

    design = _design(angles)
    condition = float(np.linalg.cond(design))
    if condition > MAX_DESIGN_CONDITION:
        msg = (
            f"angle set is degenerate for two-harmonic separation (condition {condition:.3g} > "
            f"{MAX_DESIGN_CONDITION:.3g}). Angles clustered, or spaced so that cos 4a repeats "
            f"wherever cos 2a does, cannot tell the geometries apart at all."
        )
        raise ValueError(msg)

    grid = frames.shape[1:]
    observations = frames.reshape(n_angles, -1)
    coefficients, *_ = np.linalg.lstsq(design, observations, rcond=None)
    residuals = observations - design @ coefficients

    # sigma per pixel from the joint fit's own residuals, not from an assumed noise model.
    dof = max(n_angles - design.shape[1], 1)
    sigma_sq = np.sum(residuals**2, axis=0) / dof

    # cov = sigma**2 (A.T A)**-1. The diagonal gives each coefficient its variance; the two
    # entries of a harmonic pair are averaged, because the fitted amplitude combines them.
    gram_inverse = np.linalg.inv(design.T @ design)
    var_2 = 0.5 * (gram_inverse[1, 1] + gram_inverse[2, 2])
    var_4 = 0.5 * (gram_inverse[3, 3] + gram_inverse[4, 4])

    # Amplitude of a pure-noise cos/sin pair is Rayleigh distributed with E = s sqrt(pi/2).
    # This is the same arithmetic as finding N2's anisotropy floor, in its natural units.
    rayleigh = np.sqrt(np.pi / 2.0)
    floor_2 = np.sqrt(sigma_sq * var_2) * rayleigh
    floor_4 = np.sqrt(sigma_sq * var_4) * rayleigh

    amplitude_2 = np.hypot(coefficients[1], coefficients[2])
    amplitude_4 = np.hypot(coefficients[3], coefficients[4])

    snr_2_map = np.divide(amplitude_2, floor_2, out=np.zeros_like(amplitude_2), where=floor_2 > 0)
    snr_4_map = np.divide(amplitude_4, floor_4, out=np.zeros_like(amplitude_4), where=floor_4 > 0)

    # Decide on the pixels that modulate. Ranking on the larger of the two amplitudes avoids
    # assuming the answer: ranking on the 2nd harmonic alone would pick the pixels that best
    # fit the geometry we are trying to test for.
    strength = np.maximum(amplitude_2, amplitude_4)
    n_pixels = strength.size
    n_keep = max(1, round(modulating_fraction * n_pixels))
    selected = np.argpartition(strength, n_pixels - n_keep)[n_pixels - n_keep :]

    snr_2 = float(np.median(snr_2_map[selected]))
    snr_4 = float(np.median(snr_4_map[selected]))

    has_2 = snr_2 >= detection_snr
    has_4 = snr_4 >= detection_snr
    if has_2 and has_4:
        verdict = HarmonicVerdict.BOTH
    elif has_2:
        verdict = HarmonicVerdict.SECOND
    elif has_4:
        verdict = HarmonicVerdict.FOURTH
    else:
        verdict = HarmonicVerdict.NEITHER

    return HarmonicSignature(
        amplitude_2=amplitude_2.reshape(grid),
        amplitude_4=amplitude_4.reshape(grid),
        floor_2=floor_2.reshape(grid),
        floor_4=floor_4.reshape(grid),
        dc=coefficients[0].reshape(grid),
        n_angles=n_angles,
        verdict=verdict,
        snr_2=snr_2,
        snr_4=snr_4,
        detection_snr=detection_snr,
    )
