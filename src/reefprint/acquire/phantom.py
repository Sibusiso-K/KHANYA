"""A synthetic polished section with analytically known Stokes parameters.

This is a test instrument, not a simulation of mineralogy. Its only job is to produce a
rotation series whose correct answer is known in closed form, so that a bug in
:mod:`reefprint.polarim` cannot hide behind "well, real rocks are messy". Everything it knows
about real minerals is one bit per phase — isotropic or not — and that bit comes from crystal
symmetry, which is not in dispute.

**Every number here is labelled with where it came from.** Rule 1 is not satisfied by putting
a comment somewhere; the provenance travels with the value, and
``test_no_placeholder_value_is_reported_as_measured`` in the test suite fails if a
:data:`Provenance.PLACEHOLDER` value ever escapes into something presented as a measurement.
Replacing the placeholders is a lookup in the IMA/COM Quantitative Data File, not a judgement
call — see ``docs/03-free-stack.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

import numpy as np

from reefprint.acquire.series import RotationSeries
from reefprint.polarim.stokes import StokesImage, intensity_at_angle

if TYPE_CHECKING:
    import numpy.typing as npt

    FloatArray = npt.NDArray[np.floating]

__all__ = ["PHASES", "Phantom", "Phase", "Provenance", "synthetic_rotation_series"]


class Provenance(StrEnum):
    """Where a number came from. Attached to the number, not to a comment near it."""

    CONSTITUTION = "CLAUDE.md physics table"
    SYMMETRY = "crystal symmetry — cubic phases are isotropic by definition"
    PLACEHOLDER = "PLACEHOLDER — pending IMA/COM Quantitative Data File lookup"


@dataclass(frozen=True, slots=True)
class Phase:
    """One phase in the phantom, with the provenance of each of its two numbers.

    ``anisotropy`` is the degree of linear polarisation the phase produces under analyser
    rotation: exactly 0 for a cubic mineral, non-zero for an anisotropic one. It is the
    quantity the week-1 gate is about.
    """

    name: str
    label: int
    reflectance_pct: float
    reflectance_provenance: Provenance
    anisotropy: float
    anisotropy_provenance: Provenance
    aolp_deg: float = 0.0

    @property
    def is_measured(self) -> bool:
        """False if either number is still a placeholder. Nothing quantitative may cite it."""
        return Provenance.PLACEHOLDER not in (
            self.reflectance_provenance,
            self.anisotropy_provenance,
        )


#: The phantom's phases.
#:
#: Chromite and gangue reflectances are the values stated in the constitution. The sulphide
#: reflectances are placeholders and are marked as such — the *gate* does not depend on them,
#: because what separates pentlandite from pyrrhotite here is anisotropy, not brightness. That
#: is the point of the project: they are hard to tell apart by reflectance alone.
PHASES: tuple[Phase, ...] = (
    Phase(
        name="gangue/resin",
        label=0,
        reflectance_pct=4.75,  # CLAUDE.md: R ~ 4.5-5%
        reflectance_provenance=Provenance.CONSTITUTION,
        anisotropy=0.0,
        anisotropy_provenance=Provenance.PLACEHOLDER,
    ),
    Phase(
        name="pentlandite",
        label=1,
        reflectance_pct=50.0,
        reflectance_provenance=Provenance.PLACEHOLDER,
        anisotropy=0.0,  # cubic -> isotropic, dark through a full rotation
        anisotropy_provenance=Provenance.SYMMETRY,
    ),
    Phase(
        name="pyrrhotite",
        label=2,
        reflectance_pct=38.0,
        reflectance_provenance=Provenance.PLACEHOLDER,
        anisotropy=0.12,  # CLAUDE.md says "moderate"; the magnitude is a guess
        anisotropy_provenance=Provenance.PLACEHOLDER,
        aolp_deg=20.0,
    ),
    Phase(
        name="chalcopyrite",
        label=3,
        reflectance_pct=44.0,
        reflectance_provenance=Provenance.PLACEHOLDER,
        anisotropy=0.03,  # CLAUDE.md says "weakly"; the magnitude is a guess
        anisotropy_provenance=Provenance.PLACEHOLDER,
        aolp_deg=70.0,
    ),
    Phase(
        name="chromite",
        label=4,
        reflectance_pct=13.0,  # CLAUDE.md: R ~ 13%
        reflectance_provenance=Provenance.CONSTITUTION,
        anisotropy=0.0,  # cubic -> isotropic
        anisotropy_provenance=Provenance.SYMMETRY,
    ),
)


@dataclass(frozen=True, slots=True)
class Phantom:
    """A rotation series together with the answer it should produce."""

    series: RotationSeries
    labels: npt.NDArray[np.integer]
    truth: StokesImage
    phases: tuple[Phase, ...]

    def mask(self, name: str) -> npt.NDArray[np.bool_]:
        """Pixels belonging to the named phase."""
        for phase in self.phases:
            if phase.name == name:
                return self.labels == phase.label
        msg = f"no phase named {name!r}; have {[p.name for p in self.phases]}"
        raise KeyError(msg)


def _grain_field(
    shape: tuple[int, int],
    phases: tuple[Phase, ...],
    grains_per_phase: int,
    rng: np.random.Generator,
) -> npt.NDArray[np.integer]:
    """Circular grains of each non-background phase scattered on a gangue matrix."""
    height, width = shape
    labels = np.zeros(shape, dtype=np.int16)
    yy, xx = np.ogrid[:height, :width]
    radius = min(shape) / 12.0

    for phase in phases[1:]:
        for _ in range(grains_per_phase):
            cy = rng.uniform(radius, height - radius)
            cx = rng.uniform(radius, width - radius)
            grain_radius = radius * rng.uniform(0.6, 1.3)
            labels[(yy - cy) ** 2 + (xx - cx) ** 2 <= grain_radius**2] = phase.label
    return labels


def synthetic_rotation_series(
    *,
    n_angles: int = 36,
    shape: tuple[int, int] = (192, 256),
    noise_pct: float = 0.0,
    grains_per_phase: int = 6,
    seed: int = 0,
    phases: tuple[Phase, ...] = PHASES,
) -> Phantom:
    """Build a rotation series whose Stokes parameters are known exactly.

    Args:
        n_angles: Analyser positions, spread evenly over 180 degrees. The modulation has period
            pi, so a half turn is a full cycle — 36 angles is a 5-degree step, matching the
            protocol LumenStone's XPL rotations use over 360.
        shape: Pixel grid, ``(height, width)``.
        noise_pct: Standard deviation of additive Gaussian noise, in the same R% units as the
            frames. Zero gives an exactly invertible series.
        grains_per_phase: Circular grains scattered per non-background phase.
        seed: Seeds grain placement and noise, so a failing test reproduces exactly.
        phases: Phase definitions. The first entry is the matrix.

    Returns:
        A :class:`Phantom` carrying the series, the label map, and the true Stokes image.
    """
    rng = np.random.default_rng(seed)
    labels = _grain_field(shape, phases, grains_per_phase, rng)

    s0 = np.zeros(shape, dtype=float)
    magnitude = np.zeros(shape, dtype=float)
    aolp = np.zeros(shape, dtype=float)
    for phase in phases:
        selected = labels == phase.label
        s0[selected] = phase.reflectance_pct
        magnitude[selected] = phase.anisotropy * phase.reflectance_pct
        aolp[selected] = np.radians(phase.aolp_deg)

    truth = StokesImage(
        s0=s0,
        s1=magnitude * np.cos(2.0 * aolp),
        s2=magnitude * np.sin(2.0 * aolp),
        residual_rms=np.zeros(shape, dtype=float),
        n_angles=n_angles,
    )

    angles = np.linspace(0.0, np.pi, n_angles, endpoint=False)
    frames = np.stack([intensity_at_angle(truth, angle) for angle in angles])
    if noise_pct > 0:
        frames = frames + rng.normal(0.0, noise_pct, size=frames.shape)

    series = RotationSeries(
        frames=frames,
        angles_rad=angles,
        source=f"synthetic phantom (seed={seed}, noise={noise_pct} R%)",
        units="R%",
        metadata={
            "synthetic": True,
            "illumination_schedule": "frozen — constant, no adaptation",
            "placeholder_phases": [p.name for p in phases if not p.is_measured],
        },
    )
    return Phantom(series=series, labels=labels, truth=truth, phases=phases)
