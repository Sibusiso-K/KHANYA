"""Integration scope: optional transport stays out of the default install; advisory provenance
is recorded either way. The OPC UA tests need the ``integrate`` extra (``uv sync --extra
integrate``) — they skip cleanly without it rather than failing collection for a developer who
has not installed ``asyncua``.
"""

from __future__ import annotations

import asyncio

import pytest

from reefprint.integrate.advisory import AdvisoryRecord

asyncua = pytest.importorskip("asyncua", reason="OPC UA tests need `uv sync --extra integrate`")

from reefprint.integrate.opcua_client import (  # noqa: E402
    AppliedAdvisory,
    RefusedStaleAdvisory,
    SimulatedControlClient,
)
from reefprint.integrate.opcua_server import AdvisoryServer  # noqa: E402


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


def test_advisory_record_refuses_non_finite_values_and_a_dead_validity_window():
    """Rule 1 at the transport boundary: a NaN or a non-positive window must not construct."""
    with pytest.raises(ValueError, match="finite"):
        AdvisoryRecord(values={"x": float("nan")}, advisory_influenced=False, source="s")
    with pytest.raises(ValueError, match="positive"):
        AdvisoryRecord(
            values={"x": 0.1}, advisory_influenced=False, source="s", valid_for_seconds=0.0
        )


def test_opc_ua_server_exposes_advisory_values():
    """A real local OPC UA server publishes advisory values; a separate simulated control
    client reads them over the wire and applies them — then, on a second record emitted in the
    past, refuses to apply a stale one. This is CLAUDE.md's brief deliverable: 'integrates with
    existing sorting or flotation controls', demonstrated with the acknowledgement-and-expiry
    contract and never a controller replacing MillStar/FloatStar (asyncua is LGPL-3.0 — general-
    purpose machine only, never a sealed appliance. SBOM.md, gauntlet finding S3).
    """
    asyncio.run(_server_round_trip())


async def _server_round_trip() -> None:
    now = 1_700_000_000.0

    async with AdvisoryServer() as server:
        fresh = AdvisoryRecord(
            values={"fine_chromite_risk": 0.62},
            advisory_influenced=False,
            source="test_opc_ua_server_exposes_advisory_values",
            unit="fraction",
            emitted_at=now,
            valid_for_seconds=300.0,
        )
        published = await server.publish(fresh)
        assert published == ("fine_chromite_risk",)
        assert server.published_heads == ("fine_chromite_risk",)

        node_ids = server.node_ids_for("fine_chromite_risk")

        async with SimulatedControlClient(server.endpoint_url) as client:
            # Read shortly after emission: well inside the 300 s validity window.
            outcome = await client.poll_and_apply("fine_chromite_risk", node_ids, now=now + 5.0)
            assert isinstance(outcome, AppliedAdvisory)
            assert outcome.value == pytest.approx(0.62)
            assert client.parameter("fine_chromite_risk").value == pytest.approx(0.62)
            assert client.parameter("fine_chromite_risk").history == [0.0, 0.62]

            # A new record, emitted far enough in the past that its own window has lapsed.
            stale = AdvisoryRecord(
                values={"fine_chromite_risk": 0.91},
                advisory_influenced=False,
                source="test_opc_ua_server_exposes_advisory_values",
                unit="fraction",
                emitted_at=now,
                valid_for_seconds=300.0,
            )
            await server.publish(stale)

            outcome = await client.poll_and_apply("fine_chromite_risk", node_ids, now=now + 301.0)
            assert isinstance(outcome, RefusedStaleAdvisory)
            assert outcome.age_seconds == pytest.approx(301.0)
            assert outcome.valid_for_seconds == pytest.approx(300.0)

            # The refusal must not have moved the simulated parameter at all — no fallback to
            # holding a "last known" value through the client, which would just relocate rule
            # 5's failure mode one layer up rather than closing it.
            assert client.parameter("fine_chromite_risk").value == pytest.approx(0.62)
            assert client.parameter("fine_chromite_risk").history == [0.0, 0.62]
