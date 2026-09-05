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


def test_approximate_references_do_not_claim_verified_qdf_records():
    """An internal approximate table cannot masquerade as a published measurement."""
    assert qdf_value("chromite").value == pytest.approx(13.0)
    assert qdf_value("gangue/resin").value == pytest.approx(4.75)
    assert "not a verified QDF record" in qdf_value("chromite").cite()
    assert qdf_value("chromite").provenance.name == "ASSUMED"
    assert qdf_value("gangue/resin").provenance.name == "ASSUMED"


def test_dark_and_flat_field_correction_precede_reflectance():
    """Vignetting and sensor dark current bias R% systematically, not randomly."""
    corrected = correct_counts(
        np.array([[110.0, 210.0]]), dark_counts=10.0, flat_field=np.array([[1.0, 2.0]])
    )
    assert corrected == pytest.approx(np.array([[100.0, 100.0]]))
