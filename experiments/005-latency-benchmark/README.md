# 005 — Latency on the shipped REEFPRINT-side path

**Status: two stages measured, on named hardware, with a spread. The full brief-shaped pipeline
is not measured — see *What this does not show*.**

```bash
uv sync --extra integrate
uv run python experiments/005-latency-benchmark/run.py
```

Writes `output/latency-report.md`, overwriting it each run. That file is **not committed**
(`experiments/**/output/` is gitignored, same convention as experiment 001's PNG) — the numbers
of record for a given commit live in this README and in `docs/BUILDLOG.md`.

## What it does

Times two stages of the shipped path with `reefprint.trust.latency.measure_stage`, which runs
each stage 20–30 times (after 3 discarded warm-up calls) and reports mean, median, p95 and
standard deviation — never a single best-case number:

1. **The Stokes inversion** — `stokes_from_rotation_series` on a synthetic phantom, at two
   representative sizes (64×96 and 192×256, the shapes the offline demo and the week-1 gate
   actually use).
2. **The OPC UA advisory round trip** — publish an `AdvisoryRecord` on a real local
   `AdvisoryServer` (P1), then connect, read, and disconnect, per call. A fresh connection every
   time is the worst case a non-persistent client hits, not a best case a kept-open connection
   would show.

## Result (this machine, this commit)

Run the script to regenerate `output/latency-report.md` locally. As of the run that shipped this
experiment: Stokes inversion at 64×96 runs a few milliseconds
per call; at 192×256 (36 angles, the week-1 gate's default) it runs roughly a tenth of a second
per call, on ordinary laptop-class hardware with no GPU involved. The OPC UA round trip,
including a fresh TCP connection each time, runs in the same rough range as the smaller Stokes
inversion.

## What this does NOT show

**No segmentation inference, no image decode, no postprocess.** Those stages are KHANYA's, on
`main`, behind a trained DeepLabv3+ResNet50 checkpoint — the technical review of 2026-09-12
confirmed the validated checkpoint was absent from the clone it inspected too, and it is absent
from this checkout as well. **This experiment therefore does not, and cannot yet, support a
"real-time" claim about the brief's literal pipeline** (decode → inference → postprocess →
advisory emit). It supports a narrower, true claim: two specific stages of the shipped path run
fast enough on ordinary hardware that they are very unlikely to be the bottleneck, whichever
number the segmentation stage turns out to need.

**Closing this properly needs a matching benchmark run on `main`**, using the same
`reefprint.trust.latency` instrument (importable from `main` via the bridge pattern, same as
`polarimetry.py`), reported in the same table, before anyone says "real-time" in the talk.

## Why a bound, not a threshold

This experiment reports numbers. It does not assert a pass/fail latency bar, because CLAUDE.md
rule 10 says state the limitation before anyone asks, and "is 105 ms per Stokes inversion
'real-time'?" depends on the control loop's actual cycle time — a plant-specific fact this
repository does not have, and should not invent one to answer the question.
