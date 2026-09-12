"""Rule 4's discipline applied to a timing claim: a latency number needs its spread and a named
piece of hardware, not a best case. The brief says "real-time"; before this module, nothing in
either half of the repository had ever measured a number to check that against.

**Percentile, not mean, is the number a control loop cares about.** A mean latency of 40 ms with
an occasional 400 ms tail is not "fast on average" to an operator watching a refusal fire late —
it is a system that is usually fast and unpredictably not. :attr:`LatencyMeasurement.p95` is
reported alongside the mean for exactly this reason, and both are reported with :attr:`n`, the
honest sample size, because a mean over three runs and a mean over three hundred are not the
same claim even when the two numbers happen to match.

**What this module measures, and what it structurally cannot.** :class:`LatencyMeasurement`
times whatever callable it is given; it does not know what pipeline stage that callable
represents. The caller — see ``tests/test_latency.py`` and
``experiments/005-latency-benchmark/`` — is responsible for naming every stage of the shipped
path it did *not* measure, in the same report that quotes the stages it did. Segmentation
inference lives on KHANYA's ``main`` branch behind a trained checkpoint this checkout does not
carry (the technical review of 2026-09-12 confirms the checkpoint is absent here too); a latency
number for that stage would have to come from `main`, not from this module pretending to
estimate it.
"""

from __future__ import annotations

import platform
import time
from collections.abc import Callable
from dataclasses import dataclass
from statistics import mean, median, stdev

__all__ = ["LatencyMeasurement", "current_hardware_description", "measure_stage"]


@dataclass(frozen=True, slots=True)
class LatencyMeasurement:
    """Per-call durations for one pipeline stage, on named hardware.

    :param stage: what was timed. Free text, but specific — "stokes inversion, 64x96 phantom",
        never just "inference".
    :param seconds: one duration per call, in the order measured. Never averaged before
        construction — :attr:`n`, :attr:`mean_seconds` and :attr:`p95_seconds` are derived from
        this, not supplied separately, so they cannot drift out of sync with the raw data.
    :param hardware: what ran it. See :func:`current_hardware_description` for a default that
        does not require the caller to guess what is worth recording.
    """

    stage: str
    seconds: tuple[float, ...]
    hardware: str

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("a latency measurement must name its stage")
        if not self.hardware.strip():
            raise ValueError(
                "a latency measurement must name its hardware — a number with no hardware "
                "attached cannot be compared against anything, including a re-run of itself"
            )
        if len(self.seconds) == 0:
            raise ValueError("cannot measure a stage with zero timed calls")
        if any(not (s >= 0.0) for s in self.seconds):
            raise ValueError("a duration cannot be negative — got a bad clock read")

    @property
    def n(self) -> int:
        """Honest sample size — the count actually timed, never assumed."""
        return len(self.seconds)

    @property
    def mean_seconds(self) -> float:
        return mean(self.seconds)

    @property
    def median_seconds(self) -> float:
        return median(self.seconds)

    @property
    def stdev_seconds(self) -> float | None:
        """``None`` at ``n < 2`` — a spread computed from one sample is not a spread."""
        if self.n < 2:
            return None
        return stdev(self.seconds)

    @property
    def p95_seconds(self) -> float:
        """The 95th-percentile duration — the tail a control loop actually has to tolerate.

        Nearest-rank method on the sorted samples: no interpolation invented between two real
        measurements. At small ``n`` this is necessarily coarse (at ``n = 10`` it is simply the
        10th, i.e. worst, sample) — :meth:`summary` states ``n`` alongside it so that coarseness
        is visible rather than implied.
        """
        ordered = sorted(self.seconds)
        index = max(0, min(self.n - 1, round(0.95 * self.n) - 1))
        return ordered[index]

    def summary(self) -> str:
        spread = f"{self.stdev_seconds * 1000:.2f} ms" if self.stdev_seconds is not None else "n/a"
        return (
            f"{self.stage}: mean {self.mean_seconds * 1000:.2f} ms (sd {spread}), "
            f"median {self.median_seconds * 1000:.2f} ms, p95 {self.p95_seconds * 1000:.2f} ms, "
            f"n = {self.n}, on {self.hardware}"
        )


def measure_stage(
    fn: Callable[[], object],
    *,
    stage: str,
    hardware: str | None = None,
    n: int = 30,
    warmup: int = 3,
) -> LatencyMeasurement:
    """Time ``n`` calls to ``fn`` with :func:`time.perf_counter`, after ``warmup`` discarded calls.

    :param warmup: calls run and timed *not at all* before the measured ones, so import-time
        caching, JIT warm-up, or first-call filesystem effects do not appear as false latency.
        Set to ``0`` for a stage where the *cold* call is the one that matters (e.g. genuinely
        one-shot start-up cost) — that is a deliberate choice the caller states, not a default.
    :param n: how many timed calls to make. Reported back as :attr:`LatencyMeasurement.n`; there
        is no hidden minimum here because refusing on too-small n is :mod:`reefprint.trust`'s
        pattern for *inference* (see :data:`~reefprint.heads.falsification.
        MIN_LOCALITIES_FOR_INFERENCE`), and a raw timing report is not an inference — it is the
        measuring instrument itself, and honest n is stated, not gated.
    """
    if n < 1:
        raise ValueError("must time at least one call")
    resolved_hardware = hardware if hardware is not None else current_hardware_description()

    for _ in range(warmup):
        fn()

    durations: list[float] = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        durations.append(time.perf_counter() - start)

    return LatencyMeasurement(stage=stage, seconds=tuple(durations), hardware=resolved_hardware)


def current_hardware_description() -> str:
    """A one-line description of the machine this process is running on.

    Not a benchmark of the hardware itself — just enough to say what a number was measured on,
    so a re-run on different hardware is never silently compared against this one.
    """
    return (
        f"{platform.system()} {platform.release()}, "
        f"{platform.machine()}, Python {platform.python_version()}"
    )
