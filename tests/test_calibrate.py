"""Placeholder — reefprint.calibrate."""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.calibrate.reflectance import ReflectanceStandard, correct_counts, qdf_value


def test_counts_convert_to_quantitative_reflectance():
    """Raw camera counts to R% against a reflectance standard, per wavelength."""
    standard = ReflectanceStandard("white tile", 550, np.array([1000.0, 1010.0]), 100.0)
    result = standard.convert(np.array([130.0, 130.0]))
    assert np.mean(result) == pytest.approx(12.94, rel=1e-3)


def test_known_minerals_land_near_published_qdf_values():
    """Chromite near R = 13%, gangue/resin near R = 4.5-5%.

    The IMA/COM Quantitative Data File is the teacher. This test is what stops the pipeline
    from being self-consistent and wrong.
    """
    assert qdf_value("chromite").value == pytest.approx(13.0)
    assert qdf_value("gangue/resin").value == pytest.approx(4.75)
    assert qdf_value("chromite").provenance.value.startswith("a published")


def test_dark_and_flat_field_correction_precede_reflectance():
    """Vignetting and sensor dark current bias R% systematically, not randomly."""
    corrected = correct_counts(
        np.array([[110.0, 210.0]]), dark_counts=10.0, flat_field=np.array([[1.0, 2.0]])
    )
    assert corrected == pytest.approx([[100.0, 100.0]])
