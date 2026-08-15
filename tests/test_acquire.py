"""Placeholder — reefprint.acquire. Week-1 gate, input half."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_rotation_series_has_uniform_angular_sampling():
    """Acquire I(theta) over a full analyser rotation at a known, uniform angular step.

    Uniform sampling is not cosmetic: the Stokes recovery in reefprint.polarim is a Fourier
    projection onto cos(2 theta) and sin(2 theta), and unequal spacing biases it.
    """
    pytest.fail("NOT BUILT — acquire: rotation-series acquisition")


def test_illumination_schedule_is_frozen_for_training_capture():
    """Gauntlet blind spot 6: adaptive illumination is a leakage channel.

    Acquisition state correlates with collection time, which correlates with labels. Any
    capture flagged as training data must carry a frozen, recorded schedule.
    """
    pytest.fail("NOT BUILT — acquire: frozen illumination schedule for training capture")


def test_acquisition_metadata_records_provenance():
    """Every capture carries instrument, standard, wavelength, exposure and angle set.

    Rule 1: an R% with no traceable acquisition state is an invented number.
    """
    pytest.fail("NOT BUILT — acquire: acquisition metadata")
