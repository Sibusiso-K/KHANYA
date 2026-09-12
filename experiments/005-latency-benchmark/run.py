"""Experiment 005 — latency on the shipped REEFPRINT-side path.

Run: uv run python experiments/005-latency-benchmark/run.py
Needs: uv sync --extra integrate (asyncua, for the OPC UA stage)

Writes experiments/005-latency-benchmark/output/latency-report.md.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from asyncua import Client

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.integrate.advisory import AdvisoryRecord
from reefprint.integrate.opcua_server import AdvisoryServer
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.trust.latency import LatencyMeasurement, current_hardware_description, measure_stage

OUTPUT = Path(__file__).parent / "output" / "latency-report.md"

#: Shapes named in CLAUDE.md's design target range are out of scope (ADR-0002); these are
#: representative phantom sizes actually exercised by the test suite and the offline demo.
STOKES_SHAPES = ((64, 96), (192, 256))
N_CALLS = 30
N_OPC_UA_CALLS = 20


def measure_stokes_stage(shape: tuple[int, int]) -> LatencyMeasurement:
    phantom = synthetic_rotation_series(noise_pct=0.25, shape=shape, seed=20260912)

    def invert() -> None:
        stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad, project=True)

    height, width = shape
    return measure_stage(
        invert, stage=f"Stokes inversion, {height}x{width} phantom, 36 angles", n=N_CALLS
    )


async def measure_opc_ua_stage() -> LatencyMeasurement:
    async with AdvisoryServer() as server:
        record = AdvisoryRecord(
            values={"fine_chromite_risk": 0.5},
            advisory_influenced=False,
            source="experiment 005 latency benchmark",
        )
        await server.publish(record)
        node_ids = server.node_ids_for("fine_chromite_risk")

        durations: list[float] = []
        for _ in range(N_OPC_UA_CALLS):
            start = time.perf_counter()
            async with Client(url=server.endpoint_url) as client:
                await client.get_node(node_ids.value).read_value()
            durations.append(time.perf_counter() - start)

        return LatencyMeasurement(
            stage="OPC UA advisory publish+connect+read round trip",
            seconds=tuple(durations),
            hardware=current_hardware_description(),
        )


def main() -> None:
    measurements = [measure_stokes_stage(shape) for shape in STOKES_SHAPES]
    measurements.append(asyncio.run(measure_opc_ua_stage()))

    hardware = current_hardware_description()
    lines = [
        "# Experiment 005 — latency, REEFPRINT-side path",
        "",
        f"**Hardware:** {hardware}",
        "**Generated:** this file is overwritten on every run and is not committed "
        "(`experiments/**/output/` is gitignored, same as experiment 001) — the numbers of "
        "record live in `README.md` and `docs/BUILDLOG.md`, quoted at the commit that "
        "produced them.",
        "",
        "## What this measures",
        "",
        "Two stages of the shipped path that run entirely on this branch: the linear-Stokes",
        "inversion (the physics measurement), and the OPC UA advisory publish-then-read round",
        "trip built for P1 (a fresh connection per read — the worst case a non-persistent",
        "client hits, not a best case).",
        "",
        "## What this does NOT measure",
        "",
        "**Segmentation inference, image decode, and postprocess.** Those stages live on",
        "KHANYA's `main` branch behind a trained checkpoint (DeepLabv3+ResNet50) that this",
        "checkout does not carry — the technical review of 2026-09-12 confirmed the validated",
        "checkpoint is absent from the clone it inspected too. A latency number for those stages",
        "must come from a benchmark run on `main`, reported alongside this one, never estimated",
        "here. **No end-to-end 'real-time' claim is made by this report** — it is one input to",
        "that claim, not the claim itself.",
        "",
        "## Results",
        "",
        "| Stage | n | mean | median | p95 | sd |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m in measurements:
        sd = f"{m.stdev_seconds * 1000:.2f} ms" if m.stdev_seconds is not None else "n/a"
        lines.append(
            f"| {m.stage} | {m.n} | {m.mean_seconds * 1000:.2f} ms | "
            f"{m.median_seconds * 1000:.2f} ms | {m.p95_seconds * 1000:.2f} ms | {sd} |"
        )
    lines += [
        "",
        "## Raw summaries",
        "",
        "```",
        *[m.summary() for m in measurements],
        "```",
        "",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    for m in measurements:
        print(m.summary())
    print(f"\nWritten to {OUTPUT}")


if __name__ == "__main__":
    main()
