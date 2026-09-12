"""Linear Stokes recovery from a rotating-analyser series.

An ideal linear analyser at angle ``theta`` in front of the detector passes

    I(theta) = (S0 + S1 cos 2 theta + S2 sin 2 theta) / 2

which is Malus's law generalised to partially polarised light. Three or more analyser angles
that are distinct modulo pi therefore determine (S0, S1, S2) per pixel.

**The illumination is unpolarised, and that is not a detail** (ADR-0005). No polariser sits in
the illumination path: unpolarised light reaches the specimen and the analyser is the only
polarising element, in front of the detector. The polarisation we measure is *generated on
reflection*, by differential reflectance between the grain's two eigen-axes.

    incident        grain                    reflected                       DOLP
    unpolarised     isotropic, r1 == r2      unpolarised                     0    -> no modulation
    unpolarised     anisotropic, r1 != r2    partially linearly polarised    (|r1|^2 - |r2|^2)
                                             along the eigen-axes            / (|r1|^2 + |r2|^2)

So an isotropic phase shows no modulation as the analyser turns and an anisotropic one does.
Pentlandite is cubic and stays flat through a full rotation; pyrrhotite has moderate
bireflectance and lights up.

**The counterexample that pins this, and why the arrangement must be stated.** Put a fixed
polariser in the illumination path instead and the conclusion inverts. At normal incidence an
isotropic medium has ``r_s == r_p``, so its Jones matrix is ``r * I`` and reflection preserves
the linear azimuth: incident linear light returns linear light at the same azimuth, giving
``(S0, S1, S2) = (I0, I0, 0)``, ``DOLP = 1`` and ``I(theta) = I0 cos^2(theta)`` — *full*
modulation, from a cubic mineral. An isotropic grain that "stays dark through a full rotation"
is an observation about **specimen rotation between fixed crossed polars**, which is the other
row of the geometry table in :mod:`reefprint.polarim.geometry` and a different instrument.
Conflating the two is the error this module's own guard exists to prevent, and the repository
made it in prose until 2026-09-12. Pinned by
``test_an_isotropic_grain_under_a_fixed_polariser_modulates_fully``.

The normalised modulation depth,

    (I_max - I_min) / (I_max + I_min) = sqrt(S1**2 + S2**2) / S0 = DOLP

is exactly the degree of linear polarisation, so one quantity carries both the optics and the
mineralogy. That equality is what makes an anisotropy map a physical measurement rather than a
contrast stretch.

Circular polarisation (S3) is not recovered. A rotating analyser alone cannot see it — that
needs a retarder. Nothing in the week-1 gate depends on it.
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
    "StokesImage",
    "intensity_at_angle",
    "stokes_from_rotation_series",
]

#: Three unknowns (S0, S1, S2), so three independent analyser angles.
MIN_ANGLES = 3

#: Above this, the analyser angles are too close to degenerate modulo pi to invert safely.
#: The perfectly-conditioned case (angles evenly spread over pi) gives cond(A) = 1.
MAX_DESIGN_CONDITION = 1.0e3


@dataclass(frozen=True, slots=True)
class StokesImage:
    """Per-pixel linear Stokes parameters.

    ``s0``, ``s1`` and ``s2`` share a shape, which is the pixel grid — ``()`` for a single
    pixel, ``(h, w)`` for an image. Units are whatever the input intensities were in; if those
    were calibrated to R% then so are these, and if they were raw counts then so are these.
    ``reefprint.calibrate`` owns that conversion, not this module.

    ``residual_rms`` is the root-mean-square intensity left unexplained by the three-parameter
    fit. It is not decoration: a specimen that drifts, a stage that slips, or a stray reflection
    all show up here and nowhere else in the recovered parameters.
    """

    s0: FloatArray
    s1: FloatArray
    s2: FloatArray
    residual_rms: FloatArray
    n_angles: int

    @property
    def linear_magnitude(self) -> FloatArray:
        """``sqrt(S1**2 + S2**2)`` — the amplitude of the modulation under analyser rotation."""
        return np.hypot(self.s1, self.s2)

    @property
    def dolp(self) -> FloatArray:
        """Degree of linear polarisation, in [0, 1] for any physically realisable state.

        Zero where ``s0`` is zero: an unilluminated pixel has no polarisation state to report,
        and 0/0 must not become a NaN that propagates silently into a mineral map.
        """
        raw = np.divide(
            self.linear_magnitude,
            self.s0,
            out=np.zeros_like(self.s0),
            where=self.s0 > 0,
        )
        return np.clip(raw, 0.0, 1.0)

    @property
    def anisotropy(self) -> FloatArray:
        """The anisotropy map. Identical to :attr:`dolp`, named for what it measures.

        Equal to ``(I_max - I_min) / (I_max + I_min)`` over the analyser rotation, which is the
        normalised bireflectance contrast of classical ore microscopy. Same number, two
        vocabularies: keep both names so the physics and the mineralogy stay connected.
        """
        return self.dolp

    @property
    def aolp_rad(self) -> FloatArray:
        """Angle of linear polarisation in radians, wrapped to [0, pi).

        The half-angle is not a convention choice: (S1, S2) rotate at twice the physical angle,
        so the polarisation direction is only defined modulo pi.
        """
        return 0.5 * np.arctan2(self.s2, self.s1) % np.pi

    @property
    def is_physical(self) -> npt.NDArray[np.bool_]:
        """``True`` where ``S0 >= sqrt(S1**2 + S2**2)`` and ``S0 >= 0``.

        A recovered state outside the cone is not an exotic specimen, it is a bad fit — noise,
        saturation, a slipped stage. Rule 5: surface it, do not quietly clip and carry on.
        """
        return (self.s0 >= 0) & (self.linear_magnitude <= self.s0 * (1 + 1e-9))

    def project_to_physical(self) -> StokesImage:
        """Scale (S1, S2) back onto the physical cone where the fit escaped it.

        Preserves the angle of polarisation and ``S0``; only the magnitude is reduced. Use
        :attr:`is_physical` on the *unprojected* result to count how often this was needed —
        a projection rate that is not near zero means the acquisition is the problem.
        """
        magnitude = self.linear_magnitude
        s0 = np.maximum(self.s0, 0.0)
        scale = np.divide(s0, magnitude, out=np.ones_like(magnitude), where=magnitude > s0)
        return StokesImage(
            s0=s0,
            s1=self.s1 * scale,
            s2=self.s2 * scale,
            residual_rms=self.residual_rms,
            n_angles=self.n_angles,
        )


def _design_matrix(angles_rad: FloatArray) -> FloatArray:
    """Rows of ``[1, cos 2 theta, sin 2 theta] / 2`` — the forward model, once per angle."""
    doubled = 2.0 * np.asarray(angles_rad, dtype=float)
    return 0.5 * np.stack([np.ones_like(doubled), np.cos(doubled), np.sin(doubled)], axis=1)


def intensity_at_angle(stokes: StokesImage, angle_rad: float | FloatArray) -> FloatArray:
    """Forward model: predict I(theta) from a Stokes image.

    The inverse of :func:`stokes_from_rotation_series`, and the reason its round-trip can be
    tested rather than believed.
    """
    doubled = 2.0 * np.asarray(angle_rad, dtype=float)
    return 0.5 * (stokes.s0 + stokes.s1 * np.cos(doubled) + stokes.s2 * np.sin(doubled))


def stokes_from_rotation_series(
    intensities: FloatArray,
    angles_rad: FloatArray,
    *,
    project: bool = False,
) -> StokesImage:
    """Recover per-pixel linear Stokes parameters from a rotating-analyser series.

    Args:
        intensities: Shape ``(n_angles, *pixel_shape)``. One frame per analyser position.
        angles_rad: Shape ``(n_angles,)``. Analyser angle of each frame, in radians. Need not
            be uniformly spaced — the fit is least squares, not a Fourier sum — but must be
            distinct modulo pi, because ``cos 2 theta`` and ``sin 2 theta`` have period pi.
        project: Project the result back onto the physical cone. Defaults to ``False`` so the
            caller sees the raw fit and can measure how often it left the cone; pass ``True``
            only once that rate has been looked at.

    Returns:
        A :class:`StokesImage` over the pixel grid.

    Raises:
        ValueError: Fewer than three angles, mismatched shapes, or an angle set that is
            degenerate modulo pi. All three are unrecoverable, and a plausible-looking
            anisotropy map computed from a rank-deficient fit is worse than an exception.
    """
    intensities = np.asarray(intensities, dtype=float)
    angles_rad = np.asarray(angles_rad, dtype=float)

    if not np.isfinite(intensities).all() or not np.isfinite(angles_rad).all():
        raise ValueError("intensities and angles must be finite")
    if intensities.size == 0:
        raise ValueError("intensities must contain measured pixels")

    if angles_rad.ndim != 1:
        msg = f"angles_rad must be 1-D, got shape {angles_rad.shape}"
        raise ValueError(msg)
    if intensities.ndim < 1 or intensities.shape[0] != angles_rad.size:
        msg = (
            f"intensities first axis must be the angle axis: got {intensities.shape} "
            f"against {angles_rad.size} angles"
        )
        raise ValueError(msg)
    if angles_rad.size < MIN_ANGLES:
        msg = (
            f"need at least {MIN_ANGLES} analyser angles to determine (S0, S1, S2), "
            f"got {angles_rad.size}"
        )
        raise ValueError(msg)

    design = _design_matrix(angles_rad)
    condition = float(np.linalg.cond(design))
    if not np.isfinite(condition) or condition > MAX_DESIGN_CONDITION:
        msg = (
            f"analyser angles are degenerate modulo pi (design condition number {condition:.3g} "
            f"> {MAX_DESIGN_CONDITION:g}). cos(2t) and sin(2t) have period pi, so angles such "
            f"as (0, 90, 180) degrees supply only two independent equations, not three."
        )
        raise ValueError(msg)

    pixel_shape = intensities.shape[1:]
    observed = intensities.reshape(angles_rad.size, -1)

    coefficients, *_ = np.linalg.lstsq(design, observed, rcond=None)
    residual = observed - design @ coefficients
    residual_rms = np.sqrt(np.mean(residual**2, axis=0))

    stokes = StokesImage(
        s0=coefficients[0].reshape(pixel_shape),
        s1=coefficients[1].reshape(pixel_shape),
        s2=coefficients[2].reshape(pixel_shape),
        residual_rms=residual_rms.reshape(pixel_shape),
        n_angles=int(angles_rad.size),
    )
    return stokes.project_to_physical() if project else stokes
