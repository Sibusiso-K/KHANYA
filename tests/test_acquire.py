"""reefprint.acquire — the rotation-series container and the phantom that exercises it.

The container is built and tested. The hardware-facing half of this module is not, and the
tests for it stay red on purpose: the red list is the backlog (see ``pyproject.toml``).
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.acquire.phantom import PHASES, Provenance, synthetic_rotation_series
from reefprint.acquire.series import RotationSeries, RotationSeriesSource

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


@pytest.mark.placeholder
def test_illumination_schedule_is_frozen_for_training_capture():
    """Gauntlet blind spot 6: adaptive illumination is a leakage channel.

    Acquisition state correlates with collection time, which correlates with labels. Any
    capture flagged as training data must carry a frozen, recorded schedule — and something
    has to *refuse* the capture when it does not. That refusal does not exist yet.
    """
    pytest.fail("NOT BUILT — acquire: frozen illumination schedule enforced on training capture")


@pytest.mark.placeholder
def test_acquisition_metadata_records_instrument_provenance():
    """Every capture carries instrument, reflectance standard, wavelength and exposure.

    Rule 1: an R% with no traceable acquisition state is an invented number. The container
    carries ``source``, ``units`` and free-form metadata; the required-field schema that makes
    an R% claim checkable belongs to reefprint.calibrate and is not written.
    """
    pytest.fail("NOT BUILT — acquire: required acquisition-provenance schema")


@pytest.mark.placeholder
def test_stored_rotation_series_loads_from_ome_tiff():
    """Replay a stored series — LumenStone S3 XPL rotations — through the same container.

    This is the leg of the week-1 gate that runs on real reflected-light ore data rather than
    on a phantom. Blocked on the dataset landing in data/, not on the code.
    """
    pytest.fail("NOT BUILT — acquire: OME-TIFF rotation-series reader")
