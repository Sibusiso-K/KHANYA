"""The rotation series: what every acquisition backend produces, whatever it is driven by.

One container and one protocol. A stepper turning a real analyser, a stored LumenStone XPL
rotation, and a synthetic phantom all hand back the same object, so ``reefprint.polarim`` never
learns which it was. That is the whole reason the Stokes maths can be built and tested before a
rig exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = ["RotationGeometry", "RotationSeries", "RotationSeriesSource"]

#: (angle, y, x). A 2-D array here is a single frame, which is not a series.
_FRAME_NDIM = 3


class RotationGeometry(StrEnum):
    """Which optical element turned between frames. Two different measurements, not two words.

    This is the single most dangerous piece of metadata in the project, because getting it
    wrong produces a clean-looking anisotropy map that is uniformly zero.

    :data:`ANALYSER` — polariser and specimen fixed, analyser stepped. The emergent Stokes
    vector is constant and the analyser samples it, so

        ``I(theta) = (S0 + S1 cos 2 theta + S2 sin 2 theta) / 2``

    Three unknowns, second harmonic in ``theta``. This is what :mod:`reefprint.polarim` inverts
    and it is the geometry the project's claim is about.

    :data:`SPECIMEN` — polariser and analyser fixed and crossed, *stage* rotated. This is how
    anisotropy has been observed by eye since the 1940s, and it is almost certainly how any
    published "XPL rotation sequence" was captured. With the specimen's principal reflection
    directions at ``phi`` to the polariser, the field reaching a crossed analyser is
    ``(r1 - r2) sin phi cos phi``, so

        ``I(phi) = |r1 - r2|**2 sin(2 phi)**2 / 4 = |r1 - r2|**2 (1 - cos 4 phi) / 8``

    **Fourth** harmonic, four extinctions per turn, and *no second-harmonic component at all*.
    Least-squares fitting the analyser model to it therefore returns S1 = S2 = 0 over any
    symmetric angle set: every anisotropic mineral is reported as isotropic, with no error and
    no NaN. Only ``residual_rms`` shows it. Hence :meth:`require_analyser_rotation`.

    :data:`UNKNOWN` — the default, and deliberately not :data:`ANALYSER`. A series that has not
    said how it was captured has not earned the right to be inverted. Rule 1.
    """

    ANALYSER = "rotating analyser, fixed polariser and specimen"
    SPECIMEN = "rotating specimen, fixed crossed polars"
    UNKNOWN = "UNKNOWN — acquisition geometry not recorded"


@dataclass(frozen=True, slots=True)
class RotationSeries:
    """Frames captured through a linear analyser at known angles.

    Attributes:
        frames: Shape ``(n_angles, height, width)``. Intensity, in whatever units the source
            produced — raw counts, normalised, or calibrated R%. ``reefprint.calibrate`` owns
            the conversion; this container only insists that all frames share it.
        angles_rad: Shape ``(n_angles,)``. The angle of the element that turned — see
            ``geometry``, which says *which* element that was.
        source: Where the frames came from, in one line. Goes into the OME-XML on write.
        geometry: Which element rotated. Defaults to :data:`RotationGeometry.UNKNOWN`, not to
            the convenient answer. Read :class:`RotationGeometry` before setting it.
        units: Name of the intensity unit, so a downstream R% claim can be checked rather
            than assumed. Rule 1.
        metadata: Free-form acquisition provenance. A capture destined to be training data
            must record its illumination schedule here and that schedule must be frozen —
            gauntlet blind spot 6, adaptive illumination is a leakage channel.
    """

    frames: FloatArray
    angles_rad: FloatArray
    source: str
    geometry: RotationGeometry = RotationGeometry.UNKNOWN
    units: str = "arbitrary"
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        frames = np.asarray(self.frames, dtype=float)
        angles = np.asarray(self.angles_rad, dtype=float)
        if frames.ndim != _FRAME_NDIM:
            msg = f"frames must be (n_angles, height, width), got shape {frames.shape}"
            raise ValueError(msg)
        if angles.ndim != 1 or angles.size != frames.shape[0]:
            msg = f"angles_rad {angles.shape} does not match frames {frames.shape}"
            raise ValueError(msg)
        object.__setattr__(self, "frames", frames)
        object.__setattr__(self, "angles_rad", angles)

    @property
    def n_angles(self) -> int:
        return int(self.angles_rad.size)

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel grid, ``(height, width)``."""
        return (int(self.frames.shape[1]), int(self.frames.shape[2]))

    def require_analyser_rotation(self) -> RotationSeries:
        """Return ``self``, or refuse if these frames cannot be inverted for Stokes parameters.

        Call this immediately before handing ``frames`` and ``angles_rad`` to
        :func:`reefprint.polarim.stokes.stokes_from_rotation_series`. It is the only thing
        standing between a stage-rotation series and a uniformly-zero anisotropy map.

        The failure it prevents is silent, which is why it is an exception rather than a
        warning. A crossed-polars stage rotation modulates at ``4 phi``; the analyser model
        fits ``2 theta``; the projection of one onto the other is zero. The fit succeeds, the
        result is physically realisable, every pixel reports DOLP ~ 0, and the only evidence
        is an elevated ``residual_rms`` that nothing is obliged to look at. Rule 5: no silent
        failures, and abstention must state a reason.

        Raises:
            ValueError: The geometry is :data:`RotationGeometry.SPECIMEN` or
                :data:`RotationGeometry.UNKNOWN`.
        """
        if self.geometry is RotationGeometry.ANALYSER:
            return self
        if self.geometry is RotationGeometry.SPECIMEN:
            msg = (
                f"{self.source!r} was captured by rotating the specimen under fixed crossed "
                f"polars, which modulates at 4*phi. The linear Stokes inversion fits 2*theta "
                f"and would return S1 = S2 = 0 for every anisotropic grain, silently. Convert "
                f"the geometry explicitly or use a fourth-harmonic estimator; do not relabel it."
            )
            raise ValueError(msg)
        msg = (
            f"{self.source!r} does not record which element rotated, so it cannot be inverted "
            f"for Stokes parameters. Set geometry=RotationGeometry.ANALYSER only if the "
            f"analyser turned while polariser and specimen stayed fixed. Rule 1: do not guess."
        )
        raise ValueError(msg)

    def rotated_specimen(self, phi_rad: float) -> RotationSeries:
        """The series that would have been captured with the specimen turned by ``phi_rad``.

        The frames do not change; only the angle they are labelled with does. The sign is the
        whole content of this method, so here is the derivation rather than an assertion.

        Turning the specimen by ``phi`` rotates the emergent state by ``2 phi``, giving
        ``S1' = S1 cos 2phi - S2 sin 2phi`` and ``S2' = S1 sin 2phi + S2 cos 2phi``. Substituting
        those into the forward model collapses to ``I'(theta) = I(theta - phi)``: what the
        analyser sees at ``theta`` after the turn is what it saw at ``theta - phi`` before it.
        A stored frame holding ``I(theta_k)`` therefore belongs at analyser angle
        ``theta_k + phi``, and the angle axis shifts *up*.

        Getting that sign backwards recovers ``R(-2 phi)`` — a Stokes image that is
        self-consistent, passes every realisability check, and is reflected about the analyser
        axis. ``test_specimen_rotation_rotates_stokes_by_twice_the_angle`` exists for this.

        This is a statement about the three-parameter model, in which the emergent state rotates
        rigidly. A real anisotropic grain under a *fixed* polariser does not oblige — turning it
        changes the angle between the incident vibration direction and the crystal axes, so the
        emergent state moves in a way this shift does not describe. Use it for the covariance
        property, not as a way to synthesise stage rotation from one capture.
        """
        return RotationSeries(
            frames=self.frames,
            angles_rad=self.angles_rad + phi_rad,
            source=f"{self.source} [specimen rotated {np.degrees(phi_rad):.3f} deg]",
            geometry=self.geometry,
            units=self.units,
            metadata=dict(self.metadata),
        )


@runtime_checkable
class RotationSeriesSource(Protocol):
    """Anything that can produce a rotation series.

    Implementations planned, in the order they become possible: a synthetic phantom (now, with
    analytic ground truth), a file replay of a stored series such as LumenStone S3 XPL rotations
    (now, real reflected-light data), and a hardware driver (only if a rig is ever built).
    """

    def acquire(self) -> RotationSeries: ...
