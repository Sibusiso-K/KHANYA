"""Placeholder — reefprint.calibrate."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_counts_convert_to_quantitative_reflectance():
    """Raw camera counts to R% against a reflectance standard, per wavelength."""
    pytest.fail("NOT BUILT — calibrate: counts to R%")


def test_known_minerals_land_near_published_qdf_values():
    """Chromite near R = 13%, gangue/resin near R = 4.5-5%.

    The IMA/COM Quantitative Data File is the teacher. This test is what stops the pipeline
    from being self-consistent and wrong.
    """
    pytest.fail("NOT BUILT — calibrate: QDF lookup and agreement check")


def test_dark_and_flat_field_correction_precede_reflectance():
    """Vignetting and sensor dark current bias R% systematically, not randomly."""
    pytest.fail("NOT BUILT — calibrate: dark/flat-field correction")
