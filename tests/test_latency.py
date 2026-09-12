"""P3: the brief says "real-time"; before this file nothing had ever measured a number against
that. ``reefprint.trust.latency`` is the instrument; this file exercises it on the parts of the
shipped path this branch can actually run end to end.

**Scope, stated up front (Rule 10).** This measures the REEFPRINT-side path: phantom generation,
the Stokes inversion, and the OPC UA advisory publish/read round trip. It does **not** measure
segmentation inference, decode, or postprocess — those live on KHANYA's ``main`` branch behind a
trained checkpoint this checkout does not carry. A latency claim covering the full brief-shaped
pipeline needs a number from `main` benchmarked the same way and reported alongside this one, not
invented here.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.trust.latency import LatencyMeasurement, current_hardware_description, measure_stage

asyncua = pytest.importorskip(
    "asyncua", reason="OPC UA latency test needs `uv sync --extra integrate`"
)

from asyncua import Client  # noqa: E402

from reefprint.integrate.advisory import AdvisoryRecord  # noqa: E402
from reefprint.integrate.opcua_server import AdvisoryServer  # noqa: E402


def test_latency_measurement_refuses_a_report_with_no_hardware_or_no_samples():
    with pytest.raises(ValueError, match="hardware"):
        LatencyMeasurement(stage="x", seconds=(0.1,), hardware="")
    with pytest.raises(ValueError, match="zero timed calls"):
        LatencyMeasurement(stage="x", seconds=(), hardware="a laptop")


def test_p95_is_the_worst_sample_at_small_n_and_stated_as_coarse():
    """At n = 10 the 95th percentile by nearest-rank is simply the slowest sample — this test
    pins that so the coarseness is a known property, not a surprise read off a real run.
    """
    measurement = LatencyMeasurement(
        stage="synthetic", seconds=tuple(float(i) for i in range(10)), hardware="test harness"
    )
    assert measurement.p95_seconds == pytest.approx(9.0)
    assert measurement.n == 10
    assert measurement.stdev_seconds is not None
    single = LatencyMeasurement(stage="synthetic", seconds=(1.0,), hardware="test harness")
    assert single.stdev_seconds is None


def test_the_stokes_inversion_stage_is_measured_with_a_spread_and_named_hardware():
    """The physics half of the shipped path — phantom in, Stokes image out — timed for real,
    not asserted against a threshold. There is no pass/fail latency bar in this test on
    purpose: CLAUDE.md rule 10 says state the number, not manufacture a verdict from it before
    the domain lead has seen what a real segmentation-plus-polarimetry pipeline actually costs.
    """
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=(64, 96), seed=20260912)

    def invert() -> None:
        stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad, project=True)

    measurement = measure_stage(invert, stage="stokes inversion, 64x96 phantom", n=20, warmup=3)

    assert measurement.stage == "stokes inversion, 64x96 phantom"
    assert measurement.n == 20
    assert measurement.hardware == current_hardware_description()
    assert measurement.mean_seconds > 0.0
    assert measurement.p95_seconds >= measurement.median_seconds
    # A sanity ceiling, not a real-time claim: a three-parameter least-squares fit over a
    # 64x96 phantom taking more than ten seconds per call would mean the harness itself is
    # broken (e.g. accidentally re-generating the phantom inside the timed closure).
    assert measurement.mean_seconds < 10.0


def test_the_opc_ua_advisory_round_trip_is_measured_end_to_end():
    """The transport half of the shipped path — publish an advisory, read it back over OPC UA —
    timed on the actual local server built for P1, not a mock.
    """
    asyncio.run(_measure_opc_ua_round_trip())


async def _measure_opc_ua_round_trip() -> None:
    async with AdvisoryServer() as server:
        record = AdvisoryRecord(
            values={"fine_chromite_risk": 0.5},
            advisory_influenced=False,
            source="test_latency benchmark",
        )
        await server.publish(record)
        node_ids = server.node_ids_for("fine_chromite_risk")

        durations: list[float] = []
        for _ in range(10):
            start = time.perf_counter()
            async with Client(url=server.endpoint_url) as client:
                await client.get_node(node_ids.value).read_value()
            durations.append(time.perf_counter() - start)

        measurement = LatencyMeasurement(
            stage="OPC UA advisory publish+connect+read round trip",
            seconds=tuple(durations),
            hardware=current_hardware_description(),
        )
        assert measurement.n == 10
        assert measurement.mean_seconds > 0.0
        assert measurement.p95_seconds >= measurement.median_seconds
        # This round trip includes a fresh connect per read (the worst case a stale, reconnecting
        # client would hit) — generous ceiling, sanity-checking the harness rather than the wire.
        assert measurement.mean_seconds < 5.0
