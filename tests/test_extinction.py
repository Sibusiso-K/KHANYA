"""reefprint.polarim.extinction — the fourth-harmonic estimator, and the trap it mirrors.

Two things are being pinned here. The first is that the estimator recovers what the crossed-
polars forward model put in, which is ordinary. The second is the reason it was written at all:
**the N3 failure is symmetric.** Fitting ``4 phi`` to a rotating-analyser series returns an
extinction amplitude of zero for every anisotropic grain, exactly as fitting ``2 theta`` to a
stage rotation returns zero anisotropy — same silent "everything is isotropic", opposite
direction. ``test_fitting_the_fourth_harmonic_to_an_analyser_series_is_silently_zero`` is that
proof, and it is why :meth:`RotationSeries.require_specimen_rotation` exists.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from reefprint.acquire.phantom import (
    PHASES,
    Phase,
    Provenance,
    crossed_polars_stage_series,
    synthetic_rotation_series,
)
from reefprint.acquire.series import RotationGeometry
from reefprint.polarim.extinction import (
    MIN_ANGLES,
    extinction_from_stage_series,
    intensity_at_stage_angle,
)
from reefprint.polarim.stokes import stokes_from_rotation_series

#: The two anisotropic phases in the phantom, with the orientation each was built at.
ANISOTROPIC = (("pyrrhotite", 0.12, 38.0, 20.0), ("chalcopyrite", 0.03, 44.0, 70.0))

#: Phases that are cubic by symmetry, so exactly rather than approximately dark.
CUBIC = ("pentlandite", "chromite")


def _contrast(anisotropy: float) -> float:
    """``sqrt(1+a) - sqrt(1-a)`` — the amplitude contrast the phantom builds its frames from."""
    return float(np.sqrt(1.0 + anisotropy) - np.sqrt(1.0 - anisotropy))


def _phase(
    anisotropy: float, *, reflectance: float = 38.0, aolp_deg: float = 20.0, label: int = 1
) -> Phase:
    """One test phase. Both numbers are placeholders and say so — Rule 1 travels with them."""
    return Phase(
        name=f"a={anisotropy:g} R={reflectance:g}",
        label=label,
        reflectance_pct=reflectance,
        reflectance_provenance=Provenance.PLACEHOLDER,
        anisotropy=anisotropy,
        anisotropy_provenance=Provenance.PLACEHOLDER,
        aolp_deg=aolp_deg,
    )


def _uncrossed_frames(
    reflectance: float,
    anisotropy: float,
    azimuth_rad: float,
    angles_rad: np.ndarray,
    epsilon_rad: float,
) -> np.ndarray:
    """Forward model with the analyser at ``90 + epsilon`` degrees instead of exactly crossed.

    Independent of the estimator: written straight from the reflection matrix, so a sign error
    in one is not shared by the other. At ``epsilon = 0`` it reduces to the phantom's
    ``peak * sin(2 (phi - phi0))**2``, which the tests check.

    Returns a ``(n_angles,)`` stack — one pixel, no spatial dimensions, matching the single-pixel
    idiom in ``test_polarim.py``. Every recovered quantity is then 0-d and reads as a float.
    """
    r1 = np.sqrt(reflectance * (1.0 + anisotropy))
    r2 = np.sqrt(reflectance * (1.0 - anisotropy))
    p, q = 0.5 * (r1 + r2), 0.5 * (r1 - r2)
    turned = 2.0 * (angles_rad - azimuth_rad)
    passed = -np.sin(epsilon_rad) * (p + q * np.cos(turned)) + np.cos(epsilon_rad) * q * np.sin(
        turned
    )
    return passed**2


def _stage_angles(n: int = 72) -> np.ndarray:
    """A full turn. The modulation has period 90 degrees, so this is four cycles, not one."""
    return np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)


# ----------------------------------------------------------------------------------------------
# Recovery: does it return what the forward model put in
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "anisotropy", "reflectance", "aolp_deg"), ANISOTROPIC)
def test_extinction_depth_recovers_the_analytic_value(name, anisotropy, reflectance, aolp_deg):
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=3)
    recovered = extinction_from_stage_series(stage.series.frames, stage.series.angles_rad)

    mask = stage.labels == next(p.label for p in stage.phases if p.name == name)
    assert mask.sum() > 0, f"{name} has no pixels in this phantom"

    expected = reflectance * _contrast(anisotropy) ** 2
    assert np.median(recovered.extinction_depth[mask]) == pytest.approx(expected, rel=1e-9)
    assert np.degrees(np.median(recovered.azimuth_rad[mask])) == pytest.approx(aolp_deg, abs=1e-6)


@pytest.mark.parametrize("name", CUBIC)
def test_a_cubic_phase_reads_exactly_zero_extinction_not_approximately(name):
    """``r1 = r2`` gives identically zero at every stage angle. Symmetry, not a measurement."""
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=3)
    recovered = extinction_from_stage_series(stage.series.frames, stage.series.angles_rad)

    mask = stage.labels == next(p.label for p in stage.phases if p.name == name)
    assert recovered.extinction_depth[mask].max() < 1e-12
    assert recovered.residual_rms[mask].max() < 1e-12


def test_the_forward_model_reproduces_the_frames_it_was_fitted_to():
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=1)
    recovered = extinction_from_stage_series(stage.series.frames, stage.series.angles_rad)

    predicted = np.stack(
        [intensity_at_stage_angle(recovered, angle) for angle in stage.series.angles_rad]
    )
    assert np.allclose(predicted, stage.series.frames, atol=1e-9)


@pytest.mark.parametrize(("name", "anisotropy", "reflectance", "aolp_deg"), ANISOTROPIC)
def test_bireflectance_contrast_needs_a_reflectance_measured_elsewhere(
    name, anisotropy, reflectance, aolp_deg
):
    """Given ``R_mean`` from outside, ``a`` comes back. Without it, nothing does — by design."""
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=3)
    recovered = extinction_from_stage_series(stage.series.frames, stage.series.angles_rad)
    mask = stage.labels == next(p.label for p in stage.phases if p.name == name)

    assert np.median(recovered.bireflectance_contrast(reflectance)[mask]) == pytest.approx(
        anisotropy, rel=1e-6
    )
    # Handed the wrong brightness, it returns a wrong answer rather than a warning: the argument
    # is required precisely because nothing in this geometry can check it.
    wrong = np.median(recovered.bireflectance_contrast(2.0 * reflectance)[mask])
    assert wrong != pytest.approx(anisotropy, rel=0.05)


# ----------------------------------------------------------------------------------------------
# The mirror of N3 — the reason require_specimen_rotation exists
# ----------------------------------------------------------------------------------------------


def test_fitting_the_fourth_harmonic_to_an_analyser_series_is_silently_zero():
    """N3, from the other side. Nothing raises; the residual is the only witness."""
    phantom = synthetic_rotation_series(noise_pct=0.0, seed=5)
    mask = phantom.mask("pyrrhotite")
    assert mask.sum() > 0

    # The frames genuinely modulate — this is not a test of a flat stack.
    assert np.ptp(phantom.series.frames, axis=0)[mask].min() > 0

    wrong = extinction_from_stage_series(phantom.series.frames, phantom.series.angles_rad)
    assert wrong.extinction_depth[mask].max() < 1e-9, (
        "a 2*theta series projected onto 4*phi must vanish; if it does not, the mirror failure "
        "is not the one documented"
    )
    # ...and the two witnesses that it went wrong, neither of which anything is obliged to read.
    assert wrong.residual_rms[mask].min() > 0
    assert wrong.crossing_ratio[mask].min() > 1e6

    # The same pixels, inverted with the geometry they were captured in, are strongly anisotropic.
    right = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    assert np.median(np.asarray(right.anisotropy)[mask]) == pytest.approx(0.12, rel=1e-6)


def test_an_analyser_series_is_refused_before_the_estimator_can_touch_it():
    phantom = synthetic_rotation_series(noise_pct=0.0, seed=5)
    with pytest.raises(ValueError, match="4"):
        phantom.series.require_specimen_rotation()


def test_a_series_that_never_recorded_its_geometry_is_refused_by_both_guards():
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=1)
    unlabelled = replace(stage.series, geometry=RotationGeometry.UNKNOWN)
    with pytest.raises(ValueError, match="do not guess"):
        unlabelled.require_analyser_rotation()
    with pytest.raises(ValueError, match="cannot be assumed"):
        unlabelled.require_specimen_rotation()


def test_a_stage_rotation_passes_its_own_guard_and_fails_the_other():
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=1)
    assert stage.series.require_specimen_rotation() is stage.series
    with pytest.raises(ValueError, match="4"):
        stage.series.require_analyser_rotation()


# ----------------------------------------------------------------------------------------------
# Refusals: rank, conditioning, shape
# ----------------------------------------------------------------------------------------------


def test_fewer_than_three_stage_angles_is_rejected():
    frames = np.zeros((MIN_ANGLES - 1, 2, 2))
    with pytest.raises(ValueError, match="three unknowns"):
        extinction_from_stage_series(frames, np.linspace(0.0, np.pi / 2, MIN_ANGLES - 1))


def test_angles_that_are_distinct_modulo_pi_but_degenerate_modulo_ninety_are_rejected():
    """The trap the docstring names: 0, 90, 180 degrees is three angles and one measurement."""
    angles = np.array([0.0, np.pi / 2.0, np.pi])
    with pytest.raises(ValueError, match="pi/2"):
        extinction_from_stage_series(np.zeros((3, 2, 2)), angles)


def test_frame_count_must_match_angle_count():
    with pytest.raises(ValueError, match="does not match"):
        extinction_from_stage_series(np.zeros((5, 2, 2)), _stage_angles(6))


# ----------------------------------------------------------------------------------------------
# The crossing ratio, and what it is actually sensitive to
# ----------------------------------------------------------------------------------------------


def test_crossing_ratio_is_one_when_the_polars_are_truly_crossed():
    stage = crossed_polars_stage_series(noise_pct=0.0, seed=3)
    recovered = extinction_from_stage_series(stage.series.frames, stage.series.angles_rad)
    mask = stage.labels == 2  # pyrrhotite
    assert np.median(recovered.crossing_ratio[mask]) == pytest.approx(1.0, rel=1e-9)


def test_uncrossed_polars_inflate_the_dc_and_turn_the_azimuth_without_biasing_the_depth():
    """Leakage is conspicuous in the ratio and invisible in the amplitude. That is the point."""
    reflectance, anisotropy, azimuth = 38.0, 0.12, np.radians(20.0)
    epsilon = np.radians(0.5)
    angles = _stage_angles()

    crossed = extinction_from_stage_series(
        _uncrossed_frames(reflectance, anisotropy, azimuth, angles, 0.0), angles
    )
    leaking = extinction_from_stage_series(
        _uncrossed_frames(reflectance, anisotropy, azimuth, angles, epsilon), angles
    )

    # The fitted fourth harmonic does not move. A peak-to-trough read would have.
    assert float(leaking.amplitude) == pytest.approx(float(crossed.amplitude), rel=1e-9)
    assert float(crossed.extinction_depth) == pytest.approx(
        reflectance * _contrast(anisotropy) ** 2, rel=1e-9
    )

    # The excess is exactly 2 sin^2(eps) (P/Q)^2, and P/Q ~ 2/a.
    r1 = np.sqrt(reflectance * (1.0 + anisotropy))
    r2 = np.sqrt(reflectance * (1.0 - anisotropy))
    p, q = 0.5 * (r1 + r2), 0.5 * (r1 - r2)
    assert float(leaking.crossing_ratio) == pytest.approx(
        1.0 + 2.0 * np.sin(epsilon) ** 2 * (p / q) ** 2, rel=1e-9
    )
    assert float(crossed.crossing_ratio) == pytest.approx(1.0, rel=1e-12)

    # And the azimuth is off by eps/2, which is why the ratio must be read before the azimuth.
    assert float(leaking.azimuth_rad) == pytest.approx(azimuth + epsilon / 2.0, abs=1e-9)
    # The second harmonic leakage introduces has nowhere to go but the residual.
    assert float(leaking.residual_rms) > 0
    assert float(crossed.residual_rms) < 1e-12


def test_the_leak_check_gets_sharper_exactly_where_the_extinction_gets_weaker():
    """``P/Q ~ 2/a``, so the same uncrossing is more visible on a weakly anisotropic phase.

    Useful direction, and not the obvious one: weak anisotropy is when an operator is tempted to
    uncross the polars in the first place, and that is when this catches them.
    """
    epsilon = np.radians(0.5)
    angles = _stage_angles()
    excess = {}
    for name, anisotropy, reflectance, aolp_deg in ANISOTROPIC:
        recovered = extinction_from_stage_series(
            _uncrossed_frames(reflectance, anisotropy, np.radians(aolp_deg), angles, epsilon),
            angles,
        )
        excess[name] = float(recovered.crossing_ratio) - 1.0

    assert excess["pyrrhotite"] == pytest.approx(0.042, abs=0.002)
    assert excess["chalcopyrite"] == pytest.approx(0.68, abs=0.02)
    # ~16x more sensitive on the phase whose extinction is ~16x fainter.
    assert excess["chalcopyrite"] > 10.0 * excess["pyrrhotite"]


# ----------------------------------------------------------------------------------------------
# Why the rotating analyser is still the better instrument
# ----------------------------------------------------------------------------------------------


def test_extinction_depth_is_quadratic_where_analyser_modulation_is_linear():
    """CLAUDE.md's ``2/a`` advantage, at its root: halve ``a``, lose half the DOLP but 3/4 of
    the extinction. This is the whole reason a stage archive is a fallback and not a substitute.
    """
    strong, weak = 0.12, 0.06
    angles = _stage_angles()
    depths = [
        float(
            extinction_from_stage_series(
                _uncrossed_frames(38.0, a, 0.0, angles, 0.0), angles
            ).extinction_depth
        )
        for a in (strong, weak)
    ]
    assert depths[0] / depths[1] == pytest.approx(4.0, rel=0.02)

    dolps = []
    for a in (strong, weak):
        phantom = synthetic_rotation_series(phases=(PHASES[0], _phase(a)), noise_pct=0.0, seed=2)
        stokes = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
        dolps.append(float(np.median(np.asarray(stokes.anisotropy)[phantom.labels == 1])))
    assert dolps[0] / dolps[1] == pytest.approx(2.0, rel=1e-6)


def test_extinction_depth_alone_confuses_bireflectance_with_brightness():
    """Finding N2 in a new costume: two grains of identical optics, one dark, read differently.

    Comparing raw extinction depths between minerals is the same mistake as comparing raw
    anisotropy medians, and it needs the same fix — divide by something that carries brightness.
    """
    anisotropy = 0.10
    bright, dark = 50.0, 13.0
    angles = _stage_angles()
    depth = {
        r: float(
            extinction_from_stage_series(
                _uncrossed_frames(r, anisotropy, 0.0, angles, 0.0), angles
            ).extinction_depth
        )
        for r in (bright, dark)
    }

    assert depth[bright] / depth[dark] == pytest.approx(bright / dark, rel=1e-9)
    assert depth[bright] > 3.0 * depth[dark]  # identical optics, and the trap reads 3.8x

    recovered = {
        r: float(
            extinction_from_stage_series(
                _uncrossed_frames(r, anisotropy, 0.0, angles, 0.0), angles
            ).bireflectance_contrast(r)
        )
        for r in (bright, dark)
    }
    assert recovered[bright] == pytest.approx(anisotropy, rel=1e-6)
    assert recovered[dark] == pytest.approx(anisotropy, rel=1e-6)
