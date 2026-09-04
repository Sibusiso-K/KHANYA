"""reefprint.acquire — the rotation-series container and the phantom that exercises it.

The container is built and tested. The hardware-facing half of this module is not, and the
tests for it stay red on purpose: the red list is the backlog (see ``pyproject.toml``).
"""

from __future__ import annotations

import numpy as np
import pytest
import tifffile

from reefprint.acquire.phantom import (
    PHASES,
    Provenance,
    crossed_polars_stage_series,
    synthetic_rotation_series,
)
from reefprint.acquire.series import (
    RotationGeometry,
    RotationSeries,
    RotationSeriesSource,
    require_calibration_provenance,
    require_frozen_illumination,
)
from reefprint.acquire.store import read_rotation_series, write_rotation_series
from reefprint.polarim.stokes import stokes_from_rotation_series

# ----------------------------------------------------------------------------------------------
# The container
# ----------------------------------------------------------------------------------------------


def test_rotation_series_rejects_a_single_frame():
    """A 2-D array is one capture, not a series, and inverting it would be rank-deficient."""
    with pytest.raises(ValueError, match="n_angles, height, width"):
        RotationSeries(frames=np.zeros((4, 4)), angles_rad=np.zeros(1), source="unit test")


def test_rotation_series_rejects_an_angle_count_that_does_not_match_the_frames():
    """The commonest acquisition bug: a dropped frame, silently shifting every angle label."""
    with pytest.raises(ValueError, match="does not match"):
        RotationSeries(frames=np.zeros((5, 4, 4)), angles_rad=np.zeros(6), source="unit test")


def test_rotation_series_records_its_units_rather_than_assuming_them():
    """Rule 1. An R% claim downstream has to be checkable against what the source produced."""
    series = RotationSeries(
        frames=np.zeros((3, 2, 2)), angles_rad=np.linspace(0, np.pi, 3), source="unit test"
    )
    assert series.units == "arbitrary"
    assert synthetic_rotation_series(n_angles=3, shape=(2, 2)).series.units == "R%"


def test_the_phantom_satisfies_the_acquisition_protocol_shape():
    """Any backend — phantom, stored LumenStone rotation, hardware — hands back the same object."""
    phantom = synthetic_rotation_series(n_angles=4, shape=(8, 8))
    assert isinstance(phantom.series, RotationSeries)
    assert phantom.series.shape == (8, 8)
    assert phantom.series.n_angles == 4
    assert phantom.labels.shape == phantom.series.shape

    class Replay:
        def acquire(self) -> RotationSeries:
            return phantom.series

    assert isinstance(Replay(), RotationSeriesSource)


def test_phantom_samples_half_a_turn_because_the_modulation_has_period_pi():
    """cos(2t) and sin(2t) repeat after pi, so a half turn is a full cycle of the signal.

    Uniform spacing is a conditioning choice, not a correctness requirement — the recovery is
    least squares, and ``test_recovery_does_not_require_uniform_angular_sampling`` in
    ``test_polarim.py`` proves irregular angles invert fine. What matters is that the set is
    distinct modulo pi, which even spacing over pi guarantees.
    """
    angles = synthetic_rotation_series(n_angles=36, shape=(4, 4)).series.angles_rad
    steps = np.diff(angles)

    assert angles[0] == pytest.approx(0.0)
    assert angles[-1] < np.pi  # endpoint excluded: pi is the same analyser state as 0
    assert steps == pytest.approx(np.full(35, np.pi / 36))


# ----------------------------------------------------------------------------------------------
# Rule 1 — provenance travels with the number
# ----------------------------------------------------------------------------------------------


def test_no_placeholder_value_is_reported_as_measured():
    """Rule 1, enforced rather than asserted in a comment.

    A phase whose reflectance or anisotropy is still a guess must not report ``is_measured``.
    Replacing those guesses is an IMA/COM Quantitative Data File lookup, and until it happens
    the phantom has to say so.
    """
    for phase in PHASES:
        placeholders = {
            phase.reflectance_provenance,
            phase.anisotropy_provenance,
        } & {Provenance.PLACEHOLDER}
        assert phase.is_measured is not bool(placeholders), (
            f"{phase.name} reports is_measured={phase.is_measured} with provenance "
            f"{phase.reflectance_provenance!r} / {phase.anisotropy_provenance!r}"
        )


def test_the_phantom_advertises_which_of_its_phases_are_still_guesses():
    """The provenance has to survive into the capture metadata, not stop at the constant."""
    metadata = synthetic_rotation_series(n_angles=3, shape=(4, 4)).series.metadata
    named = set(metadata["placeholder_phases"])  # type: ignore[arg-type]

    assert named == {p.name for p in PHASES if not p.is_measured}
    assert "pyrrhotite" in named, "its anisotropy magnitude is a guess and must be declared"


def test_the_isotropy_of_cubic_phases_comes_from_symmetry_not_from_a_guess():
    """The one bit the week-1 gate rests on is the one bit that is not in dispute.

    Pentlandite and chromite are cubic, so their anisotropy is exactly zero by symmetry. If
    that ever gets marked PLACEHOLDER the gate is resting on an invented number.
    """
    for name in ("pentlandite", "chromite"):
        phase = next(p for p in PHASES if p.name == name)
        assert phase.anisotropy == 0.0
        assert phase.anisotropy_provenance is Provenance.SYMMETRY


def test_the_phantom_records_a_frozen_illumination_schedule():
    """Gauntlet blind spot 6, at the level the phantom can speak to it.

    Enforcement across real captures is not built — see the placeholder below.
    """
    metadata = synthetic_rotation_series(n_angles=3, shape=(4, 4)).series.metadata
    assert metadata["synthetic"] is True
    assert "frozen" in str(metadata["illumination_schedule"])


# ----------------------------------------------------------------------------------------------
# Not built. Red on purpose.
# ----------------------------------------------------------------------------------------------


def test_illumination_schedule_is_frozen_for_training_capture():
    """Gauntlet blind spot 6: adaptive illumination is a leakage channel.

    Acquisition state correlates with collection time, which correlates with labels. Any
    capture flagged as training data must carry a frozen, recorded schedule — and something
    has to *refuse* the capture when it does not. That refusal does not exist yet.
    """
    with pytest.raises(ValueError, match="frozen"):
        require_frozen_illumination({}, training=True)
    require_frozen_illumination({"illumination_schedule": "frozen: 550 nm, 10 ms"})


def test_acquisition_metadata_records_instrument_provenance():
    """Every capture carries instrument, reflectance standard, wavelength and exposure.

    Rule 1: an R% with no traceable acquisition state is an invented number. The container
    carries ``source``, ``units`` and free-form metadata; the required-field schema that makes
    an R% claim checkable belongs to reefprint.calibrate and is not written.
    """
    metadata = {
        "instrument": "synthetic camera",
        "reflectance_standard": "white tile R=100%",
        "wavelength_nm": 550,
        "exposure": "10 ms",
    }
    require_calibration_provenance(metadata)
    incomplete = {key: value for key, value in metadata.items() if key != "wavelength_nm"}
    with pytest.raises(ValueError, match="wavelength_nm"):
        require_calibration_provenance(incomplete)


@pytest.mark.placeholder
def test_the_week_1_gate_runs_on_a_public_reflected_light_rotation_series():
    """Leg (b): the same inversion, on real ore, not on a phantom.

    The reader that replays a stored series is built and round-trip tested above. What is
    missing is the *data*: LumenStone S3 v2 has no named licence, and its rotations are XPL
    stage rotations rather than analyser rotations, which is a different measurement — see
    ``test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy``. Until a public
    analyser-rotation series exists in ``data/``, or the fourth-harmonic estimator is built,
    leg (b) is open and the week-1 gate is not closed.
    """
    pytest.fail("NOT BUILT — week-1 gate leg (b): no public analyser-rotation series in data/")


# ----------------------------------------------------------------------------------------------
# Which element rotated — the metadata whose absence fails silently
# ----------------------------------------------------------------------------------------------


def test_the_phantom_records_that_the_analyser_is_what_rotated():
    """It models a rotating analyser, so it must say so rather than leave it to be assumed."""
    series = synthetic_rotation_series(n_angles=4, shape=(4, 4)).series
    assert series.geometry is RotationGeometry.ANALYSER
    assert series.require_analyser_rotation() is series


def test_a_series_that_never_recorded_its_geometry_is_refused_rather_than_assumed():
    """The default is UNKNOWN, deliberately not the convenient answer. Rule 1."""
    series = RotationSeries(
        frames=np.zeros((4, 2, 2)),
        angles_rad=np.linspace(0.0, np.pi, 4, endpoint=False),
        source="unit test",
    )
    assert series.geometry is RotationGeometry.UNKNOWN
    with pytest.raises(ValueError, match="does not record which element rotated"):
        series.require_analyser_rotation()


def test_a_stage_rotation_is_refused_by_name_not_by_accident():
    stage = crossed_polars_stage_series(n_angles=8, shape=(4, 4), grains_per_phase=1)
    with pytest.raises(ValueError, match="modulates at 4"):
        stage.series.require_analyser_rotation()


def test_a_cubic_phase_is_exactly_dark_under_crossed_polars():
    """r1 = r2 gives identically zero at every stage angle. Symmetry, not a fitted result."""
    stage = crossed_polars_stage_series(n_angles=24, shape=(96, 128), seed=3)
    labels = stage.labels
    for name in ("pentlandite", "chromite"):
        phase = next(p for p in stage.phases if p.name == name)
        mask = labels == phase.label
        assert mask.any(), f"{name} did not get placed; the test proves nothing"
        assert np.abs(stage.series.frames[:, mask]).max() == 0.0


def test_a_crossed_polars_stage_rotation_inverts_to_zero_anisotropy():
    """The evidence for ``require_analyser_rotation``, rather than an assertion that it matters.

    A stage rotation modulates at 4*phi. The linear Stokes model fits 2*theta. The projection
    of one onto the other is zero, so pyrrhotite — which is anisotropic, and is visibly
    modulating in the frames — comes back with DOLP indistinguishable from pentlandite's.
    Nothing raises. Nothing is NaN. The whole week-1 claim quietly evaporates.

    ``residual_rms`` is the only witness, and it is pinned here at its analytic value rather
    than at "large": fitting ``I = S0/2`` to ``P(1 - cos 4 phi)/2`` recovers ``S0 = P`` and
    leaves the whole fourth harmonic behind, so ``residual_rms = P / (2 sqrt 2)``. On a genuine
    analyser series with no noise that number is zero. A third of S0 is not a rounding error,
    and nothing in the pipeline currently looks at it.
    """
    stage = crossed_polars_stage_series(n_angles=72, shape=(96, 128), seed=5)
    pyrrhotite = next(p for p in stage.phases if p.name == "pyrrhotite")
    mask = stage.labels == pyrrhotite.label
    assert mask.any()

    frames = stage.series.frames
    modulation = np.ptp(frames[:, mask], axis=0)
    assert modulation.min() > 0, "the frames really do vary — the signal is present"

    recovered = stokes_from_rotation_series(frames, stage.series.angles_rad)
    assert recovered.anisotropy[mask].max() < 1e-9, (
        "a 2-theta fit to a 4-phi signal should return exactly no anisotropy — if this ever "
        "starts passing signal through, require_analyser_rotation can be reconsidered"
    )
    assert recovered.residual_rms[mask].mean() == pytest.approx(
        recovered.s0[mask].mean() / (2 * np.sqrt(2)), rel=1e-6
    ), "the residual is the only evidence the fit failed, and it sits where the algebra says"


@pytest.mark.parametrize("name", ["pyrrhotite", "chalcopyrite"])
def test_the_rotating_analyser_wins_by_2_over_a_and_wins_most_where_it_matters(name):
    """Why the rotating analyser is the better instrument for the same physical property.

    Crossed-polars extinction depth goes as the *square* of the bireflectance contrast ``a``,
    while the rotating-analyser modulation amplitude ``a R / 2`` is linear in it. The advantage
    ratio is therefore ``2 / a`` — about 17x for pyrrhotite at a = 0.12, about 67x for
    chalcopyrite at a = 0.03.

    The direction of that is the argument: **the advantage grows as the anisotropy weakens.**
    Crossed polars is adequate for the strongly anisotropic minerals a microscopist would
    reach for it on, and gets progressively worse exactly where the discrimination is hard —
    which, for the base-metal sulphides this project is about, is where it lives.

    Both numbers rest on the phantom's placeholder anisotropies, so this is a statement about
    the geometry, not a measurement about pyrrhotite. Rule 1.
    """
    stage = crossed_polars_stage_series(n_angles=72, shape=(96, 128), seed=5)
    phase = next(p for p in stage.phases if p.name == name)
    mask = stage.labels == phase.label
    assert mask.any()

    crossed_peak = stage.series.frames[:, mask].max()
    analyser_amplitude = phase.anisotropy * phase.reflectance_pct / 2.0

    assert analyser_amplitude / crossed_peak == pytest.approx(2.0 / phase.anisotropy, rel=0.02)
    assert crossed_peak / phase.reflectance_pct < 0.005, (
        "peak signal under crossed polars is a fraction of one percent of reflectance"
    )


# ----------------------------------------------------------------------------------------------
# On disk — OME-TIFF, via tifffile (ADR-0001)
# ----------------------------------------------------------------------------------------------


def test_a_stored_rotation_series_round_trips_through_ome_tiff(tmp_path):
    """Write, read, and get the same series back — including the metadata that makes it usable."""
    original = synthetic_rotation_series(n_angles=12, shape=(24, 32), noise_pct=0.1, seed=2).series
    path = write_rotation_series(original, tmp_path / "series.ome.tif")
    restored = read_rotation_series(path)

    assert restored.shape == original.shape
    assert restored.n_angles == original.n_angles
    assert restored.angles_rad == pytest.approx(original.angles_rad)
    assert restored.geometry is original.geometry
    assert restored.units == original.units
    assert restored.source == original.source
    # float32 on disk: the fit's conditioning is set by the angle set, not the eighth decimal.
    assert restored.frames == pytest.approx(original.frames, abs=1e-4)
    for key, value in original.metadata.items():
        assert restored.metadata[key] == value


def test_a_round_tripped_series_recovers_the_same_stokes_parameters(tmp_path):
    """The point of the reader: a stored series must invert to what it inverted to before."""
    phantom = synthetic_rotation_series(n_angles=36, shape=(48, 64), noise_pct=0.25, seed=4)
    before = stokes_from_rotation_series(
        phantom.series.require_analyser_rotation().frames, phantom.series.angles_rad
    )

    path = write_rotation_series(phantom.series, tmp_path / "gate.ome.tif")
    replayed = read_rotation_series(path).require_analyser_rotation()
    after = stokes_from_rotation_series(replayed.frames, replayed.angles_rad)

    assert after.anisotropy == pytest.approx(before.anisotropy, abs=1e-4)
    assert after.s0 == pytest.approx(before.s0, abs=1e-3)


def test_the_written_file_is_ome_tiff_that_other_tools_can_open(tmp_path):
    """An open benchmark nobody else can read is not an open benchmark."""
    series = synthetic_rotation_series(n_angles=6, shape=(16, 16)).series
    path = write_rotation_series(series, tmp_path / "interop.ome.tif")

    with tifffile.TiffFile(path) as handle:
        assert handle.is_ome
        assert handle.asarray().shape == (6, 16, 16)
        assert "reefprint.acquire.store/1" in handle.ome_metadata


def test_a_stack_that_states_no_angles_refuses_to_invent_them(tmp_path):
    """Rule 1. Even spacing over pi is the natural guess and it is still a guess.

    This is the case every public dataset lands in: pixels, and nothing else.
    """
    path = tmp_path / "foreign.tif"
    tifffile.imwrite(path, np.zeros((8, 16, 16), dtype=np.float32))

    with pytest.raises(ValueError, match="does not record its rotation angles"):
        read_rotation_series(path)


def test_a_stack_that_states_no_geometry_refuses_to_assume_the_analyser_turned(tmp_path):
    path = tmp_path / "foreign.tif"
    tifffile.imwrite(path, np.zeros((8, 16, 16), dtype=np.float32))

    with pytest.raises(ValueError, match="does not record which element rotated"):
        read_rotation_series(path, angles_rad=np.linspace(0.0, np.pi, 8, endpoint=False))


def test_a_foreign_stack_loads_once_the_caller_supplies_what_the_file_could_not(tmp_path):
    """And the series then says, in its own metadata, that the caller supplied it."""
    path = tmp_path / "foreign.tif"
    tifffile.imwrite(path, np.zeros((8, 16, 16), dtype=np.float32))

    series = read_rotation_series(
        path,
        angles_rad=np.linspace(0.0, np.pi, 8, endpoint=False),
        geometry=RotationGeometry.ANALYSER,
    )
    assert series.n_angles == 8
    assert series.units == "arbitrary", "never default to R% — that is a calibration claim"
    assert "caller" in str(series.metadata["angles_supplied_by"])
    assert series.require_analyser_rotation() is series


def test_the_reader_refuses_to_pick_a_winner_when_the_file_and_the_caller_disagree(tmp_path):
    """Two sources for the angle axis is the bug, not a preference to be resolved silently."""
    series = synthetic_rotation_series(n_angles=6, shape=(8, 8)).series
    path = write_rotation_series(series, tmp_path / "series.ome.tif")

    with pytest.raises(ValueError, match="Refusing to pick a winner"):
        read_rotation_series(path, angles_rad=np.linspace(0.0, np.pi, 6, endpoint=False))

    with pytest.raises(ValueError, match="different measurements"):
        read_rotation_series(path, geometry=RotationGeometry.SPECIMEN)


def test_a_single_frame_file_is_reported_as_not_being_a_series(tmp_path):
    path = tmp_path / "one-frame.tif"
    tifffile.imwrite(path, np.zeros((16, 16), dtype=np.float32))

    with pytest.raises(ValueError, match="not a series"):
        read_rotation_series(path, geometry=RotationGeometry.ANALYSER)


def test_metadata_that_cannot_be_written_raises_rather_than_being_dropped(tmp_path):
    """Losing acquisition provenance on write is the failure OME-TIFF was chosen to prevent."""
    series = RotationSeries(
        frames=np.zeros((4, 8, 8)),
        angles_rad=np.linspace(0.0, np.pi, 4, endpoint=False),
        source="unit test",
        geometry=RotationGeometry.ANALYSER,
        metadata={"exposure": object()},
    )
    with pytest.raises(TypeError, match="exposure"):
        write_rotation_series(series, tmp_path / "lossy.ome.tif")
