"""Fourth-harmonic recovery from a crossed-polars stage rotation — leg (b)'s fallback.

Finding N3 says the public "XPL rotation sequences" are almost certainly *stage* rotations,
because that is how anisotropy has been observed since the 1940s. If that is true, the Stokes
inversion may not touch them and week-1 leg (b) needs a different estimator. This is it.

With the specimen's principal reflection directions at ``phi`` to a fixed polariser and a
crossed analyser, the transmitted field is ``(r1 - r2) sin phi cos phi``, so

    I(phi) = |r1 - r2|**2 sin(2 phi)**2 / 4 = |r1 - r2|**2 (1 - cos 4 (phi - phi0)) / 8

Three unknowns again — a DC level, and the two quadratures of the fourth harmonic — so three
stage angles distinct modulo ``pi/2`` determine it.

**What this recovers, and what it cannot.** It gives extinction depth and the extinction
azimuth: two numbers per pixel against the Stokes vector's three, and crucially the depth
arrives in *arbitrary intensity units*. Crossed polars deliberately block the unpolarised
pedestal, so there is no ``S0`` in the data and no way to normalise ``|r1 - r2|**2`` into a
bireflectance contrast without a mean reflectance measured some other way. That is not an
implementation gap — it is the geometry's actual limitation, and it is one half of why the
rotating analyser is the better instrument. :meth:`ExtinctionImage.bireflectance_contrast`
takes the missing measurement as an explicit argument rather than inventing one. Rule 1.

The other half of why: extinction depth goes as bireflectance **squared** while analyser
modulation goes as bireflectance itself, so this estimator's SNR degrades quadratically as the
anisotropy weakens. Measured on the phantom, the analyser geometry survives 38x more noise
before its signal stops being detectable — see ``experiments/002-s3v2-geometry/``. Everything
here is therefore a fallback that keeps leg (b) alive if N3 is confirmed, and never an argument
that the two geometries are equivalent. They are not, and the talk must not blur them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = [
    "MIN_ANGLES",
    "ExtinctionImage",
    "extinction_from_stage_series",
    "intensity_at_stage_angle",
]

#: Three unknowns (DC, two fourth-harmonic quadratures), so three independent stage angles.
MIN_ANGLES = 3

#: Above this the stage angles are too close to degenerate modulo pi/2 to invert safely.
#: Matches :data:`reefprint.polarim.stokes.MAX_DESIGN_CONDITION`: refuse rather than return a
#: number that looks fine. Angles evenly spread over pi/2 give cond(A) close to 1.
MAX_DESIGN_CONDITION = 1.0e3

#: ``I(phi) = |r1-r2|**2 (1 - cos 4 phi) / 8``, so the fitted fourth-harmonic amplitude is
#: ``|r1-r2|**2 / 8`` and the extinction depth is eight times it.
_DEPTH_PER_AMPLITUDE = 8.0


@dataclass(frozen=True, slots=True)
class ExtinctionImage:
    """Per-pixel fourth-harmonic content of a crossed-polars stage rotation.

    Attributes:
        dc: Fitted mean level. For ideal crossed polars this equals :attr:`amplitude` exactly,
            because ``(1 - cos 4 phi)`` has equal DC and modulation. See :attr:`crossing_ratio`.
        amplitude: Fitted fourth-harmonic magnitude, ``sqrt(A4c**2 + A4s**2)``. Proportional to
            ``|r1 - r2|**2``. Same intensity units as the input frames.
        azimuth_rad: Extinction azimuth, wrapped to ``[0, pi/2)``. The quarter-turn period is
            physical, not a convention: a stage rotation has four extinctions per revolution and
            the principal directions are indistinguishable under a 90-degree turn.
        residual_rms: Intensity left unexplained by the three-parameter fit. A slipped stage,
            drift or a stray reflection shows up here and nowhere else.
        n_angles: Stage positions the fit used. The honest n for any interval (Rule 4).
    """

    dc: FloatArray
    amplitude: FloatArray
    azimuth_rad: FloatArray
    residual_rms: FloatArray
    n_angles: int

    @property
    def extinction_depth(self) -> FloatArray:
        """``|r1 - r2|**2``, in the input's intensity units. The raw fourth-harmonic observable.

        Not a contrast and not normalised — see the module docstring. Comparing it between two
        minerals compares their bireflectance *and* their brightness at once, which is finding
        N2 in a new costume.
        """
        return _DEPTH_PER_AMPLITUDE * self.amplitude

    @property
    def crossing_ratio(self) -> FloatArray:
        """``dc / amplitude``. Exactly 1.0 for ideal crossed polars; larger means leakage.

        A free self-test, and a very sensitive one. ``(1 - cos 4 phi)`` has equal DC and
        modulation, so the ideal geometry pins this at 1 and any excess is light that reached the
        detector without going through the extinction: polars not truly crossed, the deliberate
        slight uncrossing ore microscopists use to see weak anisotropy at all, stray light, or an
        unsubtracted camera black level.

        Uncrossing by ``epsilon`` is worth working through, because the result is not the
        intuitive one. With ``P = (r1 + r2)/2`` and ``Q = (r1 - r2)/2``, the analyser at
        ``90 + epsilon`` degrees passes ``-sin eps (P + Q cos 2 phi) + cos eps Q sin 2 phi``, and
        squaring gives

            ``amplitude = Q**2 / 2``  — *independent of epsilon*
            ``dc = sin**2 eps (P**2 + Q**2/2) + cos**2 eps Q**2 / 2``
            ``azimuth = phi0 + eps/2``

        So leakage does **not** bias :attr:`extinction_depth`: the fitted fourth harmonic is
        untouched, which is the real argument for fitting the harmonic rather than reading a
        peak-to-trough range, since the range absorbs the pedestal in full. What leakage does is
        inflate this ratio, and the inflation is exact rather than approximate:

            ``crossing_ratio = 1 + 2 sin**2 eps (P/Q)**2``

        ``P/Q`` is roughly ``2/a``, so the sensitivity **grows as the anisotropy weakens** — the
        same ``2/a`` that makes the rotating analyser the better instrument, showing up here as a
        better leak detector. Half a degree of uncrossing reads 1.04 on pyrrhotite (a = 0.12) and
        1.68 on chalcopyrite (a = 0.03). Modest on the strong phase, unmissable on the weak one,
        which is the useful direction: weak anisotropy is exactly when an operator is tempted to
        uncross. Leakage also rotates the azimuth by ``eps/2`` and leaves a second-harmonic term
        the model cannot fit, which lands in :attr:`residual_rms`.

        Read it before trusting an azimuth. Values below 1 are not physical and indicate a fit
        dominated by noise.
        """
        return np.divide(
            self.dc,
            self.amplitude,
            out=np.full_like(self.amplitude, np.inf),
            where=self.amplitude > 0,
        )

    def bireflectance_contrast(self, mean_reflectance: FloatArray | float) -> FloatArray:
        """The bireflectance contrast ``a``, given a mean reflectance measured *elsewhere*.

        Crossed polars cannot supply ``mean_reflectance`` — that is the whole point of the
        geometry — so it is a required argument rather than an assumption. Supply it from a
        bright-field capture of the same field, or from ``reefprint.calibrate`` once that
        exists. Passing a guess produces a guess.

        The algebra: the phantom defines contrast as ``sqrt(1+a) - sqrt(1-a)``, whose square is
        ``2 - 2 sqrt(1 - a**2)``. With ``c**2 = extinction_depth / mean_reflectance``, inverting
        gives ``a = sqrt(1 - (1 - c**2 / 2)**2)``.

        Returns:
            ``a`` in ``[0, 1]``, clipped where noise pushes the fit outside the physical range.
            Count how often that clip fires before trusting the map — a rate that is not near
            zero means the extinction is at the noise floor, which is precisely what this
            geometry does at weak anisotropy.
        """
        reflectance = np.asarray(mean_reflectance, dtype=float)
        c_squared = np.divide(
            self.extinction_depth,
            reflectance,
            out=np.zeros_like(self.extinction_depth),
            where=reflectance > 0,
        )
        inner = np.clip(1.0 - 0.5 * c_squared, -1.0, 1.0)
        return np.sqrt(np.clip(1.0 - inner**2, 0.0, 1.0))


def _design_matrix(angles_rad: FloatArray) -> FloatArray:
    """Rows of ``[1, cos 4 phi, sin 4 phi]`` — the crossed-polars forward model, once per angle."""
    quadrupled = 4.0 * np.asarray(angles_rad, dtype=float)
    return np.stack([np.ones_like(quadrupled), np.cos(quadrupled), np.sin(quadrupled)], axis=1)


def intensity_at_stage_angle(
    extinction: ExtinctionImage, angle_rad: float | FloatArray
) -> FloatArray:
    """Forward model: predict ``I(phi)`` from an extinction image.

    The inverse of :func:`extinction_from_stage_series`, so the round trip can be tested rather
    than believed.
    """
    quadrupled = 4.0 * (np.asarray(angle_rad, dtype=float) - extinction.azimuth_rad)
    return extinction.dc - extinction.amplitude * np.cos(quadrupled)


def extinction_from_stage_series(
    frames: FloatArray,
    angles_rad: FloatArray,
) -> ExtinctionImage:
    """Recover per-pixel extinction depth and azimuth from a crossed-polars stage rotation.

    Args:
        frames: Shape ``(n_angles, *pixel_shape)``. One frame per stage position.
        angles_rad: Shape ``(n_angles,)``. Stage angle of each frame, in radians. Need not be
            uniform — the fit is least squares — but must be distinct **modulo pi/2**, because
            ``cos 4 phi`` and ``sin 4 phi`` have period ``pi/2``. A set spread over 180 degrees
            covers two full cycles, not half of one; this is the trap that makes a stage angle
            set look denser than it is.

    Returns:
        An :class:`ExtinctionImage` over the pixel grid.

    Raises:
        ValueError: Fewer than three angles, mismatched shapes, or an angle set degenerate
            modulo ``pi/2``. All three are unrecoverable, and a plausible-looking extinction map
            from a rank-deficient fit is worse than an exception.
    """
    frames = np.asarray(frames, dtype=float)
    angles_rad = np.asarray(angles_rad, dtype=float)

    if angles_rad.ndim != 1:
        msg = f"angles_rad must be 1-D, got shape {angles_rad.shape}"
        raise ValueError(msg)
    if frames.shape[0] != angles_rad.size:
        msg = f"frames {frames.shape} does not match angles_rad {angles_rad.shape}"
        raise ValueError(msg)
    if angles_rad.size < MIN_ANGLES:
        msg = (
            f"{angles_rad.size} stage angles cannot determine three unknowns; "
            f"need at least {MIN_ANGLES} distinct modulo pi/2"
        )
        raise ValueError(msg)

    design = _design_matrix(angles_rad)
    condition = float(np.linalg.cond(design))
    if not np.isfinite(condition) or condition > MAX_DESIGN_CONDITION:
        msg = (
            f"stage angles are degenerate modulo pi/2 (condition number {condition:.3g} > "
            f"{MAX_DESIGN_CONDITION:.3g}). Note the period is pi/2, not pi: angles that look "
            f"well spread over a half turn can still repeat every quarter turn."
        )
        raise ValueError(msg)

    pixel_shape = frames.shape[1:]
    flat = frames.reshape(angles_rad.size, -1)
    coefficients, *_ = np.linalg.lstsq(design, flat, rcond=None)
    residuals = flat - design @ coefficients
    residual_rms = np.sqrt(np.mean(residuals**2, axis=0))

    dc, cos_term, sin_term = coefficients
    amplitude = np.hypot(cos_term, sin_term)
    # I = dc - amplitude*cos(4(phi - phi0)) expands to cos-quadrature -amplitude*cos(4 phi0),
    # so the azimuth comes from the *negated* coefficients. Getting that sign wrong offsets
    # every extinction azimuth by 22.5 degrees, which is self-consistent and wrong.
    azimuth = np.arctan2(-sin_term, -cos_term) / 4.0 % (np.pi / 2.0)

    return ExtinctionImage(
        dc=dc.reshape(pixel_shape),
        amplitude=amplitude.reshape(pixel_shape),
        azimuth_rad=azimuth.reshape(pixel_shape),
        residual_rms=residual_rms.reshape(pixel_shape),
        n_angles=int(angles_rad.size),
    )
