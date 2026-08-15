"""reefprint.polarim — physics invariants, as properties rather than examples.

These are hypothesis tests on purpose. An invariant that holds for the three arrays you happened
to try is not an invariant, and the failure mode these guard against — an angle convention error
producing a plausible-looking anisotropy map that means nothing — is exactly the kind that
survives example-based testing.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from reefprint.acquire.phantom import PHASES, Phase, synthetic_rotation_series
from reefprint.acquire.series import RotationSeries
from reefprint.polarim.stokes import (
    MIN_ANGLES,
    StokesImage,
    intensity_at_angle,
    stokes_from_rotation_series,
)

# Physically realisable linear polarisation states, parameterised the way the physics is:
# a non-negative intensity, a degree of polarisation in [0, 1], and a direction.
reflectances = st.floats(min_value=0.5, max_value=100.0, allow_nan=False, allow_infinity=False)
degrees_of_polarisation = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
polarisation_angles = st.floats(min_value=0.0, max_value=np.pi, allow_nan=False)

#: Design-matrix condition number below which a randomly drawn angle set is worth inverting.
#: Far tighter than the module's own refusal threshold — a test that only just inverts is
#: testing the conditioning, not the physics.
WELL_CONDITIONED = 100.0


def _single_pixel(s0: float, dolp: float, aolp: float) -> StokesImage:
    magnitude = s0 * dolp
    return StokesImage(
        s0=np.array(s0),
        s1=np.array(magnitude * np.cos(2 * aolp)),
        s2=np.array(magnitude * np.sin(2 * aolp)),
        residual_rms=np.array(0.0),
        n_angles=0,
    )


def _uniform_angles(n: int) -> np.ndarray:
    """``n`` analyser positions over half a turn — the modulation has period pi."""
    return np.linspace(0.0, np.pi, n, endpoint=False)


# ----------------------------------------------------------------------------------------------
# Recovery
# ----------------------------------------------------------------------------------------------


@given(s0=reflectances, dolp=degrees_of_polarisation, aolp=polarisation_angles)
def test_stokes_recovery_inverts_malus_law(s0, dolp, aolp):
    """Forward through I(theta) = (S0 + S1 cos 2t + S2 sin 2t)/2, back, unchanged."""
    truth = _single_pixel(s0, dolp, aolp)
    angles = _uniform_angles(24)
    intensities = np.array([intensity_at_angle(truth, angle) for angle in angles])

    recovered = stokes_from_rotation_series(intensities, angles)

    assert recovered.s0 == pytest.approx(truth.s0, rel=1e-9, abs=1e-9)
    assert recovered.s1 == pytest.approx(truth.s1, rel=1e-9, abs=1e-9)
    assert recovered.s2 == pytest.approx(truth.s2, rel=1e-9, abs=1e-9)


@given(
    s0=reflectances,
    dolp=degrees_of_polarisation,
    aolp=polarisation_angles,
    n_angles=st.integers(min_value=MIN_ANGLES, max_value=72),
)
def test_recovery_works_for_any_sufficient_uniform_angle_count(s0, dolp, aolp, n_angles):
    truth = _single_pixel(s0, dolp, aolp)
    angles = _uniform_angles(n_angles)
    intensities = np.array([intensity_at_angle(truth, angle) for angle in angles])

    recovered = stokes_from_rotation_series(intensities, angles)

    assert recovered.dolp == pytest.approx(dolp, abs=1e-9)


@given(
    s0=reflectances,
    dolp=degrees_of_polarisation,
    aolp=polarisation_angles,
    offsets=st.lists(
        st.floats(min_value=0.0, max_value=np.pi, allow_nan=False),
        min_size=8,
        max_size=8,
        unique_by=lambda x: round(x, 3),
    ),
)
def test_recovery_does_not_require_uniform_angular_sampling(s0, dolp, aolp, offsets):
    """The fit is least squares, not a Fourier sum, so unevenly spaced angles are fine.

    This is what lets a stored series with a slightly irregular stage, or a hand-stepped
    microscope, be used at all.
    """
    angles = np.sort(np.asarray(offsets))
    design = np.stack([np.ones_like(angles), np.cos(2 * angles), np.sin(2 * angles)], axis=1)
    if np.linalg.cond(design) > WELL_CONDITIONED:
        pytest.skip("angles drawn too close to degenerate; covered by the degeneracy test")

    truth = _single_pixel(s0, dolp, aolp)
    intensities = np.array([intensity_at_angle(truth, angle) for angle in angles])

    recovered = stokes_from_rotation_series(intensities, angles)

    assert recovered.s0 == pytest.approx(truth.s0, rel=1e-7, abs=1e-7)


# ----------------------------------------------------------------------------------------------
# Realisability
# ----------------------------------------------------------------------------------------------


@given(s0=reflectances, dolp=degrees_of_polarisation, aolp=polarisation_angles)
def test_recovered_stokes_vector_is_physically_realisable(s0, dolp, aolp):
    """S0**2 >= S1**2 + S2**2, everywhere, for any noiseless input."""
    truth = _single_pixel(s0, dolp, aolp)
    angles = _uniform_angles(24)
    intensities = np.array([intensity_at_angle(truth, angle) for angle in angles])

    recovered = stokes_from_rotation_series(intensities, angles)

    assert bool(recovered.is_physical)


@given(s0=reflectances, dolp=degrees_of_polarisation, aolp=polarisation_angles)
def test_degree_of_linear_polarisation_is_bounded(s0, dolp, aolp):
    truth = _single_pixel(s0, dolp, aolp)
    angles = _uniform_angles(24)
    intensities = np.array([intensity_at_angle(truth, angle) for angle in angles])

    recovered = stokes_from_rotation_series(intensities, angles)

    assert 0.0 <= float(recovered.dolp) <= 1.0


def test_dolp_is_zero_rather_than_nan_where_there_is_no_light():
    """An unilluminated pixel has no polarisation state. 0/0 must not become a NaN.

    A NaN here propagates silently into a mineral map and comes out the far end as a
    confident-looking hole. Rule 5.
    """
    angles = _uniform_angles(12)
    intensities = np.zeros((angles.size, 4, 4))

    recovered = stokes_from_rotation_series(intensities, angles)

    assert np.all(np.isfinite(recovered.dolp))
    assert np.all(recovered.dolp == 0.0)


def test_projection_pulls_an_unphysical_fit_back_onto_the_cone():
    stokes = StokesImage(
        s0=np.array([1.0]),
        s1=np.array([3.0]),  # magnitude 5 against S0 = 1: impossible
        s2=np.array([4.0]),
        residual_rms=np.array([0.0]),
        n_angles=MIN_ANGLES,
    )
    assert not stokes.is_physical.all()

    projected = stokes.project_to_physical()

    assert projected.is_physical.all()
    assert projected.dolp.item() == pytest.approx(1.0)
    # The direction is preserved; only the magnitude moves.
    assert projected.aolp_rad.item() == pytest.approx(stokes.aolp_rad.item())


# ----------------------------------------------------------------------------------------------
# Rotation covariance — the angle-convention trap
# ----------------------------------------------------------------------------------------------


@given(
    s0=reflectances,
    dolp=degrees_of_polarisation,
    aolp=polarisation_angles,
    phi=st.floats(min_value=-np.pi, max_value=np.pi, allow_nan=False),
)
@settings(max_examples=50)
def test_specimen_rotation_rotates_stokes_by_twice_the_angle(s0, dolp, aolp, phi):
    """Rotating the specimen by phi rotates (S1, S2) by 2 phi; S0 and DOLP do not move.

    This is the test that catches a factor-of-two or a sign error in the angle convention —
    the single most likely way to produce an anisotropy map that looks entirely reasonable and
    is entirely wrong. It goes through ``RotationSeries.rotated_specimen`` rather than shifting
    the angle axis inline, because the sign lives in that method and a test that reimplements
    it can only ever agree with itself.
    """
    truth = _single_pixel(s0, dolp, aolp)
    angles = _uniform_angles(24)
    frames = np.array([intensity_at_angle(truth, angle) for angle in angles]).reshape(-1, 1, 1)
    series = RotationSeries(frames=frames, angles_rad=angles, source="unit test")

    before = stokes_from_rotation_series(series.frames, series.angles_rad)
    rotated = series.rotated_specimen(phi)
    after = stokes_from_rotation_series(rotated.frames, rotated.angles_rad)

    assert after.s0.item() == pytest.approx(before.s0.item(), rel=1e-9, abs=1e-9)
    assert after.dolp.item() == pytest.approx(before.dolp.item(), abs=1e-9)

    expected_s1 = before.s1 * np.cos(2 * phi) - before.s2 * np.sin(2 * phi)
    expected_s2 = before.s1 * np.sin(2 * phi) + before.s2 * np.cos(2 * phi)
    assert after.s1.item() == pytest.approx(expected_s1.item(), rel=1e-8, abs=1e-8)
    assert after.s2.item() == pytest.approx(expected_s2.item(), rel=1e-8, abs=1e-8)


# ----------------------------------------------------------------------------------------------
# Degenerate input fails loudly
# ----------------------------------------------------------------------------------------------


def test_fewer_than_three_angles_is_rejected():
    angles = np.array([0.0, np.pi / 3])
    with pytest.raises(ValueError, match="at least 3 analyser angles"):
        stokes_from_rotation_series(np.ones((2, 2, 2)), angles)


def test_angles_degenerate_modulo_pi_are_rejected():
    """0, 90, 180 degrees looks like three angles and supplies two equations.

    cos(2t) and sin(2t) have period pi, so 0 and 180 degrees are the same measurement. Silently
    least-squares-fitting a rank-deficient system here would produce an anisotropy map from
    nothing.
    """
    angles = np.radians([0.0, 90.0, 180.0])
    with pytest.raises(ValueError, match="degenerate modulo pi"):
        stokes_from_rotation_series(np.ones((3, 2, 2)), angles)


def test_frame_count_must_match_angle_count():
    with pytest.raises(ValueError, match="first axis must be the angle axis"):
        stokes_from_rotation_series(np.ones((5, 2, 2)), _uniform_angles(4))


def test_residual_rises_with_noise():
    """The residual is the only place a drifting stage or a stray reflection shows up."""
    clean = synthetic_rotation_series(noise_pct=0.0, shape=(48, 64), seed=3)
    noisy = synthetic_rotation_series(noise_pct=1.0, shape=(48, 64), seed=3)

    clean_fit = stokes_from_rotation_series(clean.series.frames, clean.series.angles_rad)
    noisy_fit = stokes_from_rotation_series(noisy.series.frames, noisy.series.angles_rad)

    assert clean_fit.residual_rms.mean() < 1e-9
    assert noisy_fit.residual_rms.mean() > 0.5


@pytest.mark.parametrize("s0", [4.75, 13.0, 50.0])
@pytest.mark.parametrize("n_angles", [12, 36])
def test_the_anisotropy_noise_floor_scales_as_one_over_reflectance(s0, n_angles):
    """A truly isotropic phase reads *non-zero* anisotropy, and dark phases read higher.

    The floor is not empirical. For evenly spaced angles the design gives
    ``cov = sigma**2 (4/n) diag(1, 2, 2)``, so S1 and S2 each carry ``sigma sqrt(8/n)`` of
    independent noise and their magnitude is Rayleigh with mean ``sigma sqrt(8/n) sqrt(pi/2)``.
    DOLP divides that by S0:

        E[DOLP | isotropic] = sigma sqrt(8/n) sqrt(pi/2) / S0

    Two consequences, and both are traps. Gangue at R = 4.75% reads ~10x the apparent
    anisotropy of pentlandite at R = 50% from the same noise, so **any fixed anisotropy
    threshold is a reflectance-dependent classifier wearing a disguise** — a discrimination
    rule fitted on bright sulphides will light up every dark grain on the section. And the
    floor falls only as ``1/sqrt(n)``, so quadrupling the analyser positions halves it: that
    is the acquisition-time budget, computable before any rig exists.
    """
    rng = np.random.default_rng(7)
    sigma = 0.25
    angles = _uniform_angles(n_angles)
    truth = _single_pixel(s0, 0.0, 0.0)

    clean = np.full((n_angles, 160, 160), intensity_at_angle(truth, angles[0]))
    frames = clean + rng.normal(0.0, sigma, size=clean.shape)
    recovered = stokes_from_rotation_series(frames, angles)

    predicted = sigma * np.sqrt(8 / n_angles) * np.sqrt(np.pi / 2) / s0
    assert recovered.anisotropy.mean() == pytest.approx(predicted, rel=0.03)


# ----------------------------------------------------------------------------------------------
# The week-1 gate
# ----------------------------------------------------------------------------------------------


def test_isotropic_phase_stays_dark_through_full_rotation():
    """**The week-1 gate.**

    Pentlandite is cubic: anisotropy at the noise floor through a full analyser rotation.
    Pyrrhotite has moderate bireflectance: it lights up. Chromite is cubic too and must stay
    dark alongside pentlandite, otherwise the map is measuring brightness, not symmetry.
    """
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=(192, 256), seed=11)
    stokes = stokes_from_rotation_series(
        phantom.series.frames, phantom.series.angles_rad, project=True
    )
    anisotropy = stokes.anisotropy

    pentlandite = anisotropy[phantom.mask("pentlandite")].mean()
    pyrrhotite = anisotropy[phantom.mask("pyrrhotite")].mean()
    chromite = anisotropy[phantom.mask("chromite")].mean()

    assert pentlandite < 0.02, "pentlandite is cubic and must stay dark"
    assert chromite < 0.05, "chromite is cubic and must stay dark"
    assert pyrrhotite > 4 * pentlandite, "pyrrhotite must light up against pentlandite"


def test_anisotropy_separates_sulphides_that_reflectance_cannot():
    """The sharp version of the gate, and the one that carries the claim.

    Give pentlandite and pyrrhotite *identical* reflectance, so brightness carries no
    information whatsoever, and check that anisotropy still separates them. If this passes,
    polarimetry is adding a genuinely orthogonal axis rather than re-describing contrast.
    """
    equal_brightness = tuple(
        p if p.name not in {"pentlandite", "pyrrhotite"} else _with_reflectance(p, 44.0)
        for p in PHASES
    )
    phantom = synthetic_rotation_series(
        noise_pct=0.25, shape=(192, 256), seed=17, phases=equal_brightness
    )
    stokes = stokes_from_rotation_series(
        phantom.series.frames, phantom.series.angles_rad, project=True
    )

    pentlandite = phantom.mask("pentlandite")
    pyrrhotite = phantom.mask("pyrrhotite")

    # Reflectance genuinely cannot tell them apart: that is the premise, so assert it.
    assert stokes.s0[pentlandite].mean() == pytest.approx(stokes.s0[pyrrhotite].mean(), rel=0.02)

    # Anisotropy can.
    assert stokes.anisotropy[pentlandite].mean() < 0.02
    assert stokes.anisotropy[pyrrhotite].mean() > 0.08


def _with_reflectance(phase: Phase, reflectance_pct: float) -> Phase:
    return replace(phase, reflectance_pct=reflectance_pct)
