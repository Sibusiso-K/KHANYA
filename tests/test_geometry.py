"""The geometry discriminator, tested against both forward models.

Finding N3 held that published "XPL rotation sequences" are almost certainly stage rotations
rather than analyser rotations. "Almost certainly" is an inference from how anisotropy has been
observed since the 1940s, and an inference is not a measurement. These tests establish that the
distinction is decidable *from the frames*, which is what turns N3 into something a file can
answer instead of an email.

Both geometries have a forward model with analytic ground truth in ``reefprint.acquire.phantom``,
so every verdict here is checked against a series whose true geometry is known by construction.
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.phantom import (
    crossed_polars_stage_series,
    synthetic_rotation_series,
)
from reefprint.acquire.series import RotationGeometry
from reefprint.polarim.geometry import (
    HarmonicVerdict,
    harmonic_signature,
)
from reefprint.polarim.stokes import intensity_at_angle, stokes_from_rotation_series

#: LumenStone S3 v2's real layout, confirmed against the archive by KHANYA's
#: ``src/polarimetry.py`` --inspect on 2026-08-20: 72 frames, 5 degree steps, full turn.
S3V2_ANGLES = np.deg2rad(np.arange(0, 360, 5, dtype=float))


def test_an_analyser_rotation_is_identified_as_a_second_harmonic() -> None:
    """The phantom turns the analyser, so the modulation must land in the 2nd harmonic."""
    phantom = synthetic_rotation_series(n_angles=36, shape=(64, 96), noise_pct=0.05, seed=3)
    signature = harmonic_signature(phantom.series.frames, phantom.series.angles_rad)

    assert signature.verdict is HarmonicVerdict.SECOND
    assert signature.geometry is RotationGeometry.ANALYSER
    assert signature.geometry is phantom.series.geometry


def test_a_stage_rotation_is_identified_as_a_fourth_harmonic() -> None:
    """The crossed-polars forward model turns the stage, so the power is at 4 phi."""
    stage = crossed_polars_stage_series(n_angles=72, shape=(64, 96), noise_pct=0.05, seed=3)
    signature = harmonic_signature(stage.series.frames, stage.series.angles_rad)

    assert signature.verdict is HarmonicVerdict.FOURTH
    assert signature.geometry is RotationGeometry.SPECIMEN
    assert signature.geometry is stage.series.geometry


def test_the_losing_harmonic_sits_at_its_own_noise_floor() -> None:
    """A harmonic that is absent must read ~1x its floor, not merely "smaller".

    This is the check that the floor is calibrated rather than decorative. If ``floor_4`` were
    wrong by a factor, the verdict would still come out right on clean data and would fail on
    noisy data, which is the worst possible place to find out.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=(64, 96), noise_pct=0.4, seed=11)
    signature = harmonic_signature(phantom.series.frames, phantom.series.angles_rad)

    assert signature.snr_4 == pytest.approx(1.0, abs=0.6)
    assert signature.snr_2 > 10.0
    assert signature.verdict is HarmonicVerdict.SECOND


def test_pure_noise_yields_no_verdict_rather_than_a_confident_one() -> None:
    """Nothing modulating means UNKNOWN, not "isotropic, therefore analyser"."""
    rng = np.random.default_rng(0)
    frames = 20.0 + rng.normal(0.0, 0.5, size=(36, 32, 32))
    signature = harmonic_signature(frames, np.linspace(0.0, np.pi, 36, endpoint=False))

    assert signature.verdict is HarmonicVerdict.NEITHER
    assert signature.geometry is RotationGeometry.UNKNOWN


def test_an_analyser_series_at_the_real_s3_v2_angle_set_is_still_read_correctly() -> None:
    """72 frames at 5 degree steps over a full turn — the layout in the archive.

    An analyser rotation has period pi, so over a full turn every frame is repeated once: the
    row for theta and the row for theta+180 are identical under ``cos 2theta``. That halves the
    independent information but leaves the design matrix's conditioning untouched, and it is
    what the archive's angle set would look like *if* the analyser had been the moving element.
    The series is synthesised at those exact angles from the phantom's own Stokes truth rather
    than generated over a half turn and relabelled, because relabelling frames is precisely the
    error this module exists to detect.
    """
    phantom = synthetic_rotation_series(n_angles=36, shape=(48, 64), seed=7)
    rng = np.random.default_rng(7)
    frames = np.stack([intensity_at_angle(phantom.truth, a) for a in S3V2_ANGLES])
    frames = frames + rng.normal(0.0, 0.05, size=frames.shape)

    signature = harmonic_signature(frames, S3V2_ANGLES)

    assert signature.verdict is HarmonicVerdict.SECOND
    assert signature.geometry is RotationGeometry.ANALYSER


def test_a_stage_series_at_the_real_s3_v2_angle_set_is_still_read_correctly() -> None:
    """The same angle set, the other geometry. ``crossed_polars_stage_series`` already steps
    over the full turn, so its 72-frame default *is* the archive's angle set."""
    stage = crossed_polars_stage_series(n_angles=72, shape=(48, 64), noise_pct=0.05, seed=7)

    assert stage.series.angles_rad == pytest.approx(S3V2_ANGLES)

    signature = harmonic_signature(stage.series.frames, stage.series.angles_rad)

    assert signature.verdict is HarmonicVerdict.FOURTH
    assert signature.geometry is RotationGeometry.SPECIMEN


def test_the_discriminator_catches_what_the_stokes_inversion_silently_misses() -> None:
    """The whole reason this module exists, end to end.

    Feed a stage rotation to the Stokes inversion and it reports every anisotropic grain as
    isotropic — no exception, no NaN, a physically realisable answer. The harmonic signature
    looks at the same frames and names the geometry correctly. Without this, KHANYA's
    ten-mineral symmetry test on S3 v2 would return a separation ratio near 1.0 and read as
    "polarimetry does not work on real ore", when what it would actually mean is "the model
    was fitted to the wrong harmonic".
    """
    stage = crossed_polars_stage_series(n_angles=72, shape=(64, 96), seed=5)
    frames, angles = stage.series.frames, stage.series.angles_rad

    pyrrhotite = next(p for p in stage.phases if p.name == "pyrrhotite")
    anisotropic = stage.labels == pyrrhotite.label

    # The frames really do modulate — this is not a dead-data artefact.
    assert np.ptp(frames[:, anisotropic], axis=0).min() > 0

    # ...and the Stokes inversion reports no anisotropy whatsoever.
    recovered = stokes_from_rotation_series(frames, angles)
    assert recovered.anisotropy[anisotropic].max() < 1e-9

    # The geometry test is not fooled.
    signature = harmonic_signature(frames, angles)
    assert signature.geometry is RotationGeometry.SPECIMEN
    assert signature.snr_4 > signature.snr_2


def test_too_few_angles_is_refused_by_name() -> None:
    frames = np.ones((4, 8, 8))
    with pytest.raises(ValueError, match="cannot separate a 2nd harmonic from a 4th"):
        harmonic_signature(frames, np.linspace(0.0, np.pi, 4, endpoint=False))


def test_an_angle_set_that_cannot_tell_the_harmonics_apart_is_refused() -> None:
    """Angles clustered into a narrow arc carry no leverage on either harmonic."""
    angles = np.deg2rad(np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5]))
    frames = np.ones((angles.size, 8, 8))
    with pytest.raises(ValueError, match="degenerate for two-harmonic separation"):
        harmonic_signature(frames, angles)


def test_the_explanation_names_both_harmonics_not_just_the_winner() -> None:
    """A verdict that only reports the winner cannot be told from one that never looked."""
    stage = crossed_polars_stage_series(n_angles=72, shape=(32, 32), seed=1)
    text = harmonic_signature(stage.series.frames, stage.series.angles_rad).explain()

    assert "2nd harmonic" in text
    assert "4th harmonic" in text
    assert "SPECIMEN" in text


def _to_eight_bit(frames: np.ndarray) -> np.ndarray:
    """Quantise a frame stack the way a real sensor and a JPEG encoder do: clip, then round.

    The clip is the whole point. Casting straight to ``uint8`` *wraps* negative values, and a
    crossed-polars stack is 46 percent negative at 5 percent noise because the signal sits on a
    near-black field. That wraparound corrupts the series so thoroughly that it destroys the 4th
    harmonic, which looks exactly like a quantisation penalty and is not one. It cost a wrong
    finding on 2026-08-20 before the clip was added.
    """
    scaled = frames / max(frames.max(), 1e-9) * 255.0
    return np.clip(np.round(scaled), 0.0, 255.0)


def test_eight_bit_quantisation_costs_neither_geometry_its_verdict() -> None:
    """The archives are 8-bit JPEG, so this has to be checked rather than hoped.

    It is a null result and it is worth keeping as one: it removes "the file format ate it" from
    the list of explanations for whatever the real archive turns out to say.
    """
    for noise_pct in (0.0, 0.01, 0.02, 0.05):
        stage = crossed_polars_stage_series(
            n_angles=72, shape=(180, 240), noise_pct=noise_pct, seed=1
        )
        analyser = synthetic_rotation_series(
            n_angles=72, shape=(180, 240), noise_pct=noise_pct, seed=1
        )
        for series in (stage.series, analyser.series):
            raw = harmonic_signature(series.frames, series.angles_rad)
            quantised = harmonic_signature(_to_eight_bit(series.frames), series.angles_rad)
            assert quantised.verdict is raw.verdict, (
                f"8-bit conversion changed the verdict at noise_pct={noise_pct}: "
                f"{raw.verdict.name} -> {quantised.verdict.name}"
            )


def test_the_analyser_geometry_survives_far_more_noise_than_the_stage_geometry() -> None:
    """The ``2/a`` advantage, measured rather than asserted - and it is the case for the rig.

    Extinction depth goes as bireflectance squared, analyser modulation as bireflectance, so
    CLAUDE.md predicts the rotating analyser's advantage is ``2/a`` and *grows* as anisotropy
    weakens. The phantom's anisotropic phases are pyrrhotite (a=0.12) and chalcopyrite (a=0.03),
    giving a predicted band of 16.7x to 66.7x.

    This is a consistency check, not a derivation: a detection-threshold ratio over a mixed field
    at a declared SNR threshold is a different quantity from a per-grain contrast ratio. The
    claim is only that the measured ratio lands inside the band the theory predicts. It is also
    why a null verdict on real data leans toward stage rotation rather than being neutral.
    """

    def highest_noise_still_detected(builder, shape=(120, 160)) -> float:
        best = 0.0
        for noise_pct in (0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0, 3.0):
            series = builder(n_angles=72, shape=shape, noise_pct=noise_pct, seed=4).series
            verdict = harmonic_signature(series.frames, series.angles_rad).verdict
            if verdict in (HarmonicVerdict.NEITHER, HarmonicVerdict.BOTH):
                return best
            best = noise_pct
        return best

    stage_limit = highest_noise_still_detected(crossed_polars_stage_series)
    analyser_limit = highest_noise_still_detected(synthetic_rotation_series)

    assert stage_limit > 0.0
    ratio = analyser_limit / stage_limit
    assert 10.0 < ratio < 100.0, (
        f"measured advantage {ratio:.0f}x sits outside the 2/a band (16.7x-66.7x) that "
        f"CLAUDE.md predicts for a=0.12 and a=0.03"
    )


def test_a_quantised_stage_rotation_still_never_reads_as_an_analyser_rotation() -> None:
    """The one failure that would be unrecoverable.

    Losing the signal is survivable - it returns NEITHER and nothing downstream runs. Being told
    the wrong geometry is not, because SECOND waves the Stokes inversion through and every
    anisotropic mineral then reports as isotropic with no error raised.
    """
    for noise_pct in (0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2):
        stage = crossed_polars_stage_series(
            n_angles=72, shape=(120, 160), noise_pct=noise_pct, seed=4
        )
        signature = harmonic_signature(_to_eight_bit(stage.series.frames), stage.series.angles_rad)
        assert signature.verdict is not HarmonicVerdict.SECOND, (
            f"a stage rotation at noise_pct={noise_pct} was reported as an analyser rotation"
        )
        assert signature.geometry is not RotationGeometry.ANALYSER
