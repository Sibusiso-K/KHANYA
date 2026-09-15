"""Cluster bootstrap confidence intervals, and a paired exact test for two conditions on the
same units — the two tools `docs/10-2026-09-14-literature-and-brief-plan.md`'s Workstream D
specified ("a section-level cluster bootstrap (~60 lines, 2,000 predeclared resamples)") and
never built, until a concrete need for both arrived from `khanya/main`'s own 2026-09-15
adversarial critique and remediation plan: does topology refinement change *which* sections a
decision-gap analysis flags, not just how many.

**Why cluster, not per-pixel.** Rule 2's whole argument — that a split or an interval must be
built from independent units, never from patches or pixels within them — applies to a bootstrap
exactly as it applies to a train/test split. Resampling pixels would treat 92.6 million
correlated observations as 92.6 million independent ones and report an interval an order of
magnitude too tight. Resampling **sections** (or whatever the honest unit of independence is —
here, sections, because LumenStone ships no locality manifest to resample by instead, the same
gap `docs/09-brief-compliance.md`'s Rule 2 row already names) is the unit this module resamples.

**Determinism, per Rule 5.** Every resample is drawn from a caller-supplied, seeded
:class:`numpy.random.Generator`. The same call with the same seed returns the same interval,
bit for bit — the property `experiments/010`'s own history shows is not automatic.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import comb
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

__all__ = [
    "BootstrapCI",
    "PairedDisagreement",
    "cluster_bootstrap_ci",
    "paired_exact_test",
]

#: The plan's own predeclared resample count — predeclared, not tuned after looking at the
#: result, which is the only way a resample count avoids becoming a second free parameter.
DEFAULT_N_RESAMPLES = 2000


@dataclass(frozen=True, slots=True)
class BootstrapCI:
    """A cluster bootstrap interval, honest about the unit it was built from.

    :param point_estimate: the statistic computed on the real (unresampled) data.
    :param low: lower bound of the percentile interval.
    :param high: upper bound of the percentile interval.
    :param confidence: the interval's nominal coverage, e.g. ``0.95``.
    :param n_units: the number of independent clusters resampled — the honest *n*, per Rule 4.
        Never the number of pixels or rows inside them.
    :param n_resamples: how many bootstrap resamples were drawn.
    """

    point_estimate: float
    low: float
    high: float
    confidence: float
    n_units: int
    n_resamples: int

    def describe(self) -> str:
        pct = round(self.confidence * 100)
        return (
            f"{self.point_estimate:.4f} ({pct}% CI [{self.low:.4f}, {self.high:.4f}], "
            f"n = {self.n_units} clusters, {self.n_resamples} resamples)"
        )


def cluster_bootstrap_ci(
    values: Sequence[float],
    *,
    statistic: Callable[[npt.NDArray[np.floating]], float] = np.mean,
    confidence: float = 0.95,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    rng: np.random.Generator,
) -> BootstrapCI:
    """A percentile bootstrap CI over independent units, resampled with replacement.

    :param values: one value per independent unit (one per section, one per locality — never
        one per pixel or per patch inside a unit). ``statistic`` is applied to each resample of
        this sequence, not to anything finer-grained; if the statistic needs per-unit weights or
        counts, fold them into ``values`` before calling this, so the resampling unit stays
        exactly the sequence's own length.
    :param statistic: reduces one resample to one number. Defaults to the mean, which is what a
        flip rate or a mean IoU both are once expressed as one value per section.
    :param confidence: nominal coverage of the returned interval.
    :param n_resamples: predeclared — see the module docstring. Passing a value chosen after
        looking at a first result defeats the point of predeclaring it; that discipline is the
        caller's to keep, not something this function can enforce.
    :param rng: a seeded generator. Required, not defaulted — an unseeded bootstrap is exactly
        the missing-tie-break failure mode `experiments/010` found the hard way (module
        docstring), moved from a grid search into a resampling loop instead.

    :raises ValueError: on fewer than 2 units (no meaningful resampling), a ``confidence`` outside
        ``(0, 1)``, or ``n_resamples`` below 1.
    """
    n_units = len(values)
    if n_units < 2:
        raise ValueError(
            f"cluster_bootstrap_ci needs at least 2 independent units to resample, got {n_units} "
            "— an interval from one unit is not an interval, it is that unit's own value again"
        )
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")
    if n_resamples < 1:
        raise ValueError(f"n_resamples must be at least 1, got {n_resamples}")

    array = np.asarray(values, dtype=np.float64)
    point_estimate = float(statistic(array))

    resample_statistics = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        resample_indices = rng.integers(0, n_units, size=n_units)
        resample_statistics[i] = statistic(array[resample_indices])

    alpha = 1.0 - confidence
    low, high = np.quantile(resample_statistics, [alpha / 2.0, 1.0 - alpha / 2.0])
    return BootstrapCI(
        point_estimate=point_estimate,
        low=float(low),
        high=float(high),
        confidence=confidence,
        n_units=n_units,
        n_resamples=n_resamples,
    )


@dataclass(frozen=True, slots=True)
class PairedDisagreement:
    """Whether two binary conditions on the *same* units disagree more than chance predicts —
    McNemar's exact test on the discordant pairs, for a sample small enough that the usual
    chi-squared approximation is not trustworthy.

    :param unit_ids: which units disagreed, split by direction — the concrete, checkable fact
        underneath the p-value. A verdict without this is exactly the kind of summary doctrine
        rule 1 exists to forbid: the aggregate without the literal span it was computed from.
    :param only_in_a: units where condition A was true and condition B was false.
    :param only_in_b: units where condition B was true and condition A was false.
    :param p_value: exact two-sided binomial test on the discordant pairs against p = 0.5.
    :param n_discordant: ``len(only_in_a) + len(only_in_b)`` — the actual sample size this test
        has to work with. Concordant units (both true or both false) carry no information about
        whether the two conditions disagree and are correctly excluded from it.
    """

    only_in_a: tuple[str, ...]
    only_in_b: tuple[str, ...]
    p_value: float

    @property
    def n_discordant(self) -> int:
        return len(self.only_in_a) + len(self.only_in_b)

    @property
    def significant_at_05(self) -> bool:
        return self.p_value < 0.05

    def describe(self) -> str:
        if self.n_discordant == 0:
            return "0 discordant pairs — the two conditions agree on every unit"
        verdict = (
            "reject 'no difference'" if self.significant_at_05 else "cannot reject 'no difference'"
        )
        power_note = (
            f" — at n = {self.n_discordant} discordant pairs this test has negligible power; "
            "a non-significant result here is 'cannot tell', not 'confirmed the same'"
            if self.n_discordant < 10
            else ""
        )
        return (
            f"{len(self.only_in_a)} only-A, {len(self.only_in_b)} only-B "
            f"({self.n_discordant} discordant), exact p = {self.p_value:.4f} — {verdict}{power_note}"
        )


def paired_exact_test(labels_a: dict[str, bool], labels_b: dict[str, bool]) -> PairedDisagreement:
    """McNemar's test, exact rather than the chi-squared approximation, for two binary labellings
    of the same units — e.g. "did this section's recommendation flip", computed once under raw
    predictions and once under refined ones.

    Under the null that the two conditions disagree in each direction equally often, each
    discordant pair is an independent coin flip; the exact two-sided p-value is the binomial tail
    probability, not an approximation that assumes a discordant-pair count large enough for a
    normal approximation to hold — which a hackathon-scale n almost never is.

    :param labels_a: unit id -> boolean outcome under condition A. Both dicts must share exactly
        the same keys — these are the same units under two conditions, not two different sets.

    :raises ValueError: if the two label sets do not cover exactly the same units.
    """
    if set(labels_a) != set(labels_b):
        only_a = set(labels_a) - set(labels_b)
        only_b = set(labels_b) - set(labels_a)
        raise ValueError(
            "paired_exact_test needs the same units under both conditions — "
            f"present only in A: {sorted(only_a)!r}; present only in B: {sorted(only_b)!r}"
        )

    only_in_a = tuple(sorted(unit for unit in labels_a if labels_a[unit] and not labels_b[unit]))
    only_in_b = tuple(sorted(unit for unit in labels_a if labels_b[unit] and not labels_a[unit]))
    n_discordant = len(only_in_a) + len(only_in_b)

    if n_discordant == 0:
        p_value = 1.0
    else:
        smaller = min(len(only_in_a), len(only_in_b))
        # Exact two-sided binomial test against p = 0.5: sum the probability of every outcome no
        # more likely than the one observed. Symmetric around n_discordant / 2, so this is twice
        # the one-sided tail from 0 up to the smaller count, capped at 1.0 for the even-split case.
        tail = sum(comb(n_discordant, k) for k in range(smaller + 1)) / (2.0**n_discordant)
        p_value = min(1.0, 2.0 * tail)

    return PairedDisagreement(only_in_a=only_in_a, only_in_b=only_in_b, p_value=p_value)
