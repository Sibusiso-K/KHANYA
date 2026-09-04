"""Integration scope: optional transport stays out; advisory provenance is recorded."""

from __future__ import annotations

import pytest

from reefprint.integrate.advisory import AdvisoryRecord

pytestmark = pytest.mark.placeholder


def test_opc_ua_server_exposes_advisory_values():
    """asyncua is LGPL-3.0: general-purpose machine only, never a sealed appliance. S3."""
    pytest.fail("NOT BUILT — integrate: OPC UA advisory")


def test_advisory_influenced_flag_is_logged_on_every_record():
    """Blind spot 10, endogeneity.

    A feedforward advisory changes the blending decisions that generate the ore it predicts.
    The flag has to exist from the first record or month-three drift is uninterpretable. It
    costs nothing now and cannot be added retrospectively.
    """
    record = AdvisoryRecord(
        values={"fine_chromite_risk": 0.4}, advisory_influenced=False, source="offline demo"
    )
    payload = record.as_dict()
    assert payload["advisory_influenced"] is False
    assert "advisory_influenced" in payload
    with pytest.raises(TypeError, match="bool"):
        AdvisoryRecord(values={}, advisory_influenced=0, source="bad fixture")
