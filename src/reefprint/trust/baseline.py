"""Rule 3, made structural: report the trivial baseline alongside every metric. Always.

*Always* is the load-bearing word, and it is the word prose cannot enforce. A metric reported
without its baselines looks exactly like a metric reported with them — minus the one number that
says whether it means anything. There is no error, no gap in the output, nothing to notice. The
omission is invisible at exactly the moment it matters most, which is on a slide.

So the baselines are a **required field with no default**. :class:`ScoredMetric` cannot be
constructed without them: forgetting is not an available mistake, it is a :class:`TypeError`.

Two baselines, because they fail differently:

**Majority class.** Predict the commonest label every time. On a UG2 section that is chromite at
50-75 vol%, so a classifier can be badly wrong about every sulphide grain — which is the part
that governs PGE deportment — and still post a number in the seventies.

**Metadata-only.** Predict from what was known before the microscope was switched on: borehole,
reef, depth, locality. If this matches the model, the imaging contributed nothing, and the
honest report is that the imaging contributed nothing. This is the baseline that is quietly
dropped, because it is the one that most often wins.

:attr:`ScoredMetric.uplift` is measured against the **strongest** baseline available, never the
weakest. Quoting the gap to majority class while metadata-only sits higher is the flattering
error, and it is flattering by exactly the amount that matters.

A baseline may be genuinely inapplicable — a dataset that ships no per-section metadata has no
metadata-only baseline to compute. That is allowed, through :class:`NotApplicable`, which
requires a stated reason. The pattern is rule 5's: the escape hatch emits a reason, never
"unknown". Both baselines inapplicable at once is refused, because that is the state rule 3
forbids — a metric with nothing to compare against.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt

__all__ = [
    "Baseline",
    "NotApplicable",
    "ScoredMetric",
    "TrivialBaselines",
    "majority_class_rate",
]


@dataclass(frozen=True, slots=True)
class NotApplicable:
    """A baseline that genuinely cannot be computed, and why.

    The reason is mandatory. An omitted baseline and an inapplicable one look identical in a
    report unless the report says which it is, and "unknown" is not a reason — rule 5.
    """

    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "a NotApplicable baseline must carry a reason. An omitted baseline and an "
                "inapplicable one are indistinguishable in a report unless the reason is stated."
            )

    def __str__(self) -> str:
        return f"not applicable ({self.reason})"


Baseline = float | NotApplicable
"""A baseline is a number, or a stated reason there isn't one. Never absent."""


@dataclass(frozen=True, slots=True)
class TrivialBaselines:
    """The two numbers that have to appear next to every metric.

    :param majority_class: score of predicting the commonest label every time.
    :param metadata_only: score of predicting from borehole, reef, depth and locality alone —
        everything known before the microscope was switched on.

    **Stated assumption: higher is better.** :attr:`strongest` takes the maximum, so an
    error-like metric (RMSE, MAE) ranks its baselines backwards here. Negate such a metric
    and its baselines before wrapping them, or the "strongest baseline" is the worst one.
    """

    majority_class: Baseline
    metadata_only: Baseline

    def __post_init__(self) -> None:
        if isinstance(self.majority_class, NotApplicable) and isinstance(
            self.metadata_only, NotApplicable
        ):
            raise ValueError(
                "at least one trivial baseline must be a number. With both inapplicable there "
                f"is no baseline at all — majority class: {self.majority_class.reason}; "
                f"metadata-only: {self.metadata_only.reason}. That is the state rule 3 forbids."
            )

    @property
    def strongest(self) -> float:
        """The highest computable baseline. The only honest thing to measure uplift against."""
        return max(
            value
            for value in (self.majority_class, self.metadata_only)
            if not isinstance(value, NotApplicable)
        )

    def describe(self) -> str:
        return (
            f"majority class {_format(self.majority_class)} · "
            f"metadata-only {_format(self.metadata_only)}"
        )


@dataclass(frozen=True, slots=True)
class ScoredMetric:
    """A metric that cannot be reported without its baselines or its honest *n*.

    :param n: honest *n* — for a locality split this is the number of **localities**, which
        :attr:`~reefprint.trust.split.LocalitySplit.n_groups` gives you. Not the number of
        sections, and not the number of patches.
    :param baselines: no default, deliberately. Rule 3 as a :class:`TypeError`.
    """

    name: str
    value: float
    n: int
    baselines: TrivialBaselines

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError(
                f"{self.name}: n = {self.n}. A metric with no n cannot carry a confidence "
                "interval, and rule 4 says every metric carries one."
            )

    @property
    def strongest_baseline(self) -> float:
        return self.baselines.strongest

    @property
    def uplift(self) -> float:
        """Gap to the strongest baseline. Negative when the baseline wins, which happens."""
        return self.value - self.strongest_baseline

    @property
    def beats_baseline(self) -> bool:
        return self.uplift > 0.0

    @property
    def noise_at_honest_n(self) -> float | None:
        """Standard error on a proportion at honest *n*, or ``None`` if this is not one.

        ``sqrt(p(1-p)/n)`` — the same arithmetic this package already quotes for conformal
        coverage SD, applied to the metric itself. Returns ``None`` outside [0, 1] because a
        binomial standard error on an RMSE or an R² is an invented number, and rule 1 forbids
        inventing numbers rather more than it forbids leaving a field empty.
        """
        if not 0.0 <= self.value <= 1.0:
            return None
        return sqrt(self.value * (1.0 - self.value) / self.n)

    @property
    def uplift_exceeds_noise(self) -> bool:
        """Whether the uplift is larger than what *n* can resolve.

        The question rule 3 sets up and rule 4 answers. A +0.02 uplift at n = 12 is a seventh
        of one standard error; it is positive, and it is nothing.
        """
        noise = self.noise_at_honest_n
        if noise is None:
            return self.beats_baseline
        return self.uplift > noise

    def summary(self) -> str:
        """One line carrying the metric, both baselines, the honest n, and the verdict.

        The verdict is spelled out in words because nobody reading a slide subtracts two
        numbers. 0.62 next to a 0.60 baseline reads as a result until something says it isn't
        — and it isn't, at n = 12, by a factor of seven.

        Three states, not two. Below the baseline; above it but inside the noise that *n*
        resolves; above it by more than that. Collapsing the middle state into either
        neighbour is how a null result gets presented as a finding.
        """
        if not self.beats_baseline:
            verdict = (
                f"does not beat the strongest baseline "
                f"({self.strongest_baseline:.3f}, uplift {self.uplift:+.3f})"
            )
        elif (noise := self.noise_at_honest_n) is not None and self.uplift <= noise:
            verdict = (
                f"uplift {self.uplift:+.3f} over the strongest baseline "
                f"({self.strongest_baseline:.3f}) is inside the ±{noise:.3f} that "
                f"n = {self.n} resolves"
            )
        else:
            verdict = (
                f"+{self.uplift:.3f} over the strongest baseline ({self.strongest_baseline:.3f})"
            )
        return (
            f"{self.name} = {self.value:.3f} (n = {self.n}) · "
            f"{self.baselines.describe()} · {verdict}"
        )


def majority_class_rate(labels: Sequence[str]) -> float:
    """Fraction of ``labels`` taken by the commonest one. The floor any classifier has to clear.

    :raises ValueError: on an empty sequence — there is no majority of nothing, and returning
        0.0 would silently hand back the most flattering baseline possible.
    """
    if len(labels) == 0:
        raise ValueError(
            "cannot compute a majority-class rate from an empty label sequence. "
            "Returning 0.0 would hand back the most flattering baseline possible."
        )
    return max(Counter(labels).values()) / len(labels)


def _format(value: Baseline) -> str:
    return str(value) if isinstance(value, NotApplicable) else f"{value:.3f}"
