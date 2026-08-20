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

Rule 4 rides along, because a metric next to its baselines still needs to say whether the gap
between them is real. The standard error on a proportion is ``sqrt(p(1-p)/n)``, which is
**exactly zero at 0 and 1** — so a metric pinned at an end would report the least informative
observation available as the most precise, and, worse, the "inside the noise" verdict below
could never fire for it. The rule of three (Hanley & Lippman-Hand 1983) covers those ends.

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
    def _is_proportion(self) -> bool:
        """Whether the binomial arithmetic applies to this metric at all.

        A balanced accuracy is a proportion. A grain-size RMSE in microns is not, and neither
        is an R² that can go negative. The distinction matters twice below: it decides whether
        a standard error means anything, and it separates *the question does not apply* from
        *the question applies and n cannot answer it*.
        """
        return 0.0 <= self.value <= 1.0

    @property
    def noise_at_honest_n(self) -> float | None:
        """Standard error on a proportion at honest *n*, or ``None`` where it means nothing.

        ``sqrt(p(1-p)/n)`` — the same arithmetic this package already quotes for conformal
        coverage SD, applied to the metric itself. Returns ``None`` outside [0, 1] because a
        binomial standard error on an RMSE or an R² is an invented number, and rule 1 forbids
        inventing numbers rather more than it forbids leaving a field empty.

        Also ``None`` **at exactly 0 and 1**, where the formula degenerates to zero and the
        least informative observation available would claim the most precision. Twelve
        localities out of twelve is not certainty. :attr:`bound_at_honest_n` covers those ends.
        """
        if not self._is_proportion or self.value in (0.0, 1.0):
            return None
        return sqrt(self.value * (1.0 - self.value) / self.n)

    @property
    def bound_at_honest_n(self) -> float | None:
        """The rule of three, for the ends where the standard error degenerates.

        Zero events in *n* trials puts the 95% upper bound at ``3/n``; *n* out of *n* puts the
        95% lower bound at ``1 - 3/n`` (Hanley & Lippman-Hand 1983). A published result, cited
        so a reader can check it, rather than a threshold chosen here.

        ``None`` away from the ends, where the standard error is the right tool, and ``None``
        when ``3/n >= 1`` — at n = 3 the bound spans the whole range, which is not a bound.
        """
        if self.value not in (0.0, 1.0):
            return None
        three_over_n = 3.0 / self.n
        if three_over_n >= 1.0:
            return None
        return three_over_n if self.value == 0.0 else 1.0 - three_over_n

    @property
    def resolution_at_honest_n(self) -> float | None:
        """How large an uplift has to be before *n* can tell it from zero.

        One standard error in the middle of the range; the distance from the point estimate to
        the rule-of-three bound at the ends, which works out to ``3/n`` at both. ``None`` when
        the question does not apply (not a proportion) or *n* cannot answer it (``3/n >= 1``).

        The two are not the same coverage — one SE is about 68%, the rule of three is 95% — so
        a metric sitting at an end is judged against a wider band than one in the middle. That
        asymmetry is deliberate and it runs in the conservative direction: the ends are where
        *n* tells you least, and a perfect score on twelve localities is the most flattering
        thing this class can be asked to report.
        """
        if (noise := self.noise_at_honest_n) is not None:
            return noise
        if (bound := self.bound_at_honest_n) is None:
            return None
        return abs(self.value - bound)

    @property
    def uplift_exceeds_noise(self) -> bool:
        """Whether the uplift is larger than what *n* can resolve.

        The question rule 3 sets up and rule 4 answers. A +0.02 uplift at n = 12 is a seventh
        of one standard error; it is positive, and it is nothing.

        Where *n* resolves nothing — a proportion pinned at an end with ``3/n >= 1`` — this is
        ``False``, because no uplift can clear a band that spans the range. Where the question
        does not apply at all, it falls back to the plain sign of the uplift.
        """
        scale = self.resolution_at_honest_n
        if scale is not None:
            return self.uplift > scale
        return False if self._is_proportion else self.beats_baseline

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
        elif not self.uplift_exceeds_noise:
            verdict = (
                f"uplift {self.uplift:+.3f} over the strongest baseline "
                f"({self.strongest_baseline:.3f}) {self._resolution_clause()}"
            )
        else:
            verdict = (
                f"+{self.uplift:.3f} over the strongest baseline ({self.strongest_baseline:.3f})"
            )
        return (
            f"{self.name} = {self.value:.3f} (n = {self.n}) · "
            f"{self.baselines.describe()} · {verdict}"
        )

    def _resolution_clause(self) -> str:
        """What *n* resolves and where the number came from, as the tail of a verdict."""
        if (noise := self.noise_at_honest_n) is not None:
            return f"is inside the ±{noise:.3f} that n = {self.n} resolves"
        if (bound := self.bound_at_honest_n) is not None:
            end = "lower" if self.value == 1.0 else "upper"
            return (
                f"is inside the {abs(self.value - bound):.3f} that n = {self.n} resolves "
                f"— 95% {end} bound {bound:.3f} by the rule of three"
            )
        return f"cannot be resolved at all: n = {self.n} resolves nothing at this end of the range"


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
