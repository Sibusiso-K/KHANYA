"""Split-conformal coverage diagnostics at the locality boundary.

The calibration set determines a prediction set whose conditional coverage is random.  Under
the continuous-score exchangeability assumption, its exact finite-sample law is
``Beta(n + 1 - l, l)``, where ``l = floor((n + 1) * alpha)``.  This module keeps that law
explicit instead of using the binomial/Wald approximation, and reports coverage separately for
each held-out locality.  Per-locality coverage is an audit: ordinary split conformal guarantees
marginal coverage, not free conditional coverage for an arbitrary locality.

The ``n`` used for the coverage band is the number of independent calibration units.  Callers
must pass one calibration unit per locality (or another explicitly exchangeable unit); counting
pixels or patches would violate the project's locality-split rule.  Held-out proportions are
checked against the corresponding Beta-Binomial predictive interval, so their finite sample noise
is not mistaken for a calibration failure.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from scipy.stats import beta, betabinom

from reefprint.trust.split import Grouped, require_locality_disjoint

__all__ = [
    "CoverageBand",
    "LocalityCoverage",
    "CoverageReport",
    "coverage_band",
    "audit_coverage_by_locality",
]


@dataclass(frozen=True, slots=True)
class CoverageBand:
    """Finite-sample band for the calibration-set conditional coverage probability."""

    n_calibration: int
    alpha: float
    confidence: float
    lower: float
    upper: float
    expected: float
    standard_deviation: float
    rank: int
    misses: int

    @property
    def nominal_coverage(self) -> float:
        """Requested marginal coverage, ``1 - alpha``."""
        return 1.0 - self.alpha

    def contains(self, coverage: float) -> bool:
        """Return whether a coverage probability lies in the Beta band.

        This is the calibration-set uncertainty only. Held-out empirical proportions should use
        :meth:`contains_observation`, which also accounts for their finite sample size.
        """
        if not 0.0 <= coverage <= 1.0 or not math.isfinite(coverage):
            raise ValueError("coverage must be a finite proportion in [0, 1]")
        return self.lower <= coverage <= self.upper

    def predictive_count_bounds(self, n_observations: int) -> tuple[int, int]:
        """Return the central predictive bounds for covered observations.

        Conditional on the calibration-set coverage probability, held-out coverage is binomial.
        Mixing that binomial with the exact Beta law gives a Beta-Binomial predictive distribution,
        so a small held-out locality is not judged against a noiseless probability interval.
        """
        if (
            not isinstance(n_observations, int)
            or isinstance(n_observations, bool)
            or n_observations < 1
        ):
            raise ValueError("n_observations must be a positive integer")
        tail = (1.0 - self.confidence) / 2.0
        lower = int(math.ceil(float(betabinom.ppf(tail, n_observations, self.rank, self.misses))))
        upper = int(
            math.floor(
                float(betabinom.ppf(1.0 - tail, n_observations, self.rank, self.misses))
            )
        )
        return max(0, lower), min(n_observations, upper)

    def contains_observation(self, n_covered: int, n_observations: int) -> bool:
        """Return whether an empirical held-out count is in the predictive interval."""
        if (
            not isinstance(n_covered, int)
            or isinstance(n_covered, bool)
            or n_covered < 0
            or n_covered > n_observations
        ):
            raise ValueError("n_covered must be an integer between zero and n_observations")
        lower, upper = self.predictive_count_bounds(n_observations)
        return lower <= n_covered <= upper


def coverage_band(
    n_calibration: int,
    *,
    alpha: float = 0.10,
    confidence: float = 0.95,
) -> CoverageBand:
    """Build the exact Beta coverage band for split conformal calibration.

    ``n_calibration`` is deliberately a count of independent calibration units, normally
    localities in this project.  The order-statistic rank is ``ceil((n+1)(1-alpha))``.  If that
    rank exceeds the calibration set, finite-sample conformal calibration would need an infinite
    threshold; refusing is safer than silently returning an unbounded prediction set.
    """
    if not isinstance(n_calibration, int) or isinstance(n_calibration, bool) or n_calibration < 1:
        raise ValueError("n_calibration must be a positive integer")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be strictly between 0 and 1")

    rank = math.ceil((n_calibration + 1) * (1.0 - alpha))
    if rank > n_calibration:
        raise ValueError(
            "calibration set is too small for this alpha: the conformal order statistic is "
            "outside the observed scores; add independent localities"
        )

    misses = n_calibration + 1 - rank
    # With rank <= n, misses is at least one for a finite, non-trivial band.
    shape_a = rank
    shape_b = misses
    expected = float(beta.mean(shape_a, shape_b))
    standard_deviation = float(beta.std(shape_a, shape_b))
    tail = (1.0 - confidence) / 2.0
    lower = float(beta.ppf(tail, shape_a, shape_b))
    upper = float(beta.ppf(1.0 - tail, shape_a, shape_b))

    return CoverageBand(
        n_calibration=n_calibration,
        alpha=alpha,
        confidence=confidence,
        lower=lower,
        upper=upper,
        expected=expected,
        standard_deviation=standard_deviation,
        rank=rank,
        misses=misses,
    )


@dataclass(frozen=True, slots=True)
class LocalityCoverage:
    """Observed prediction-set coverage for one held-out locality."""

    locality: str
    n_observations: int
    n_covered: int
    band: CoverageBand

    @property
    def coverage(self) -> float:
        return self.n_covered / self.n_observations

    @property
    def within_band(self) -> bool:
        return self.band.contains_observation(self.n_covered, self.n_observations)

    @property
    def predictive_bounds(self) -> tuple[int, int]:
        """Central predictive bounds for this locality's held-out count."""
        return self.band.predictive_count_bounds(self.n_observations)


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """Per-locality coverage results and the calibration-unit-sized band."""

    band: CoverageBand
    localities: tuple[LocalityCoverage, ...]

    @property
    def passes(self) -> bool:
        """Week-3 gate: every held-out locality is inside the declared band."""
        return bool(self.localities) and all(result.within_band for result in self.localities)

    def summary(self) -> str:
        """Render an auditable line naming every locality and the honest calibration n."""
        values = ", ".join(
            f"{item.locality}={item.coverage:.3f} ({item.n_covered}/{item.n_observations}, "
            f"predictive {item.predictive_bounds[0]}–{item.predictive_bounds[1]}, "
            f"{'inside' if item.within_band else 'outside'})"
            for item in self.localities
        )
        return (
            f"coverage nominal={self.band.nominal_coverage:.2f}, "
            f"{self.band.confidence:.0%} band=[{self.band.lower:.3f}, {self.band.upper:.3f}], "
            f"honest n = {self.band.n_calibration} calibration localities: {values}"
        )


def audit_coverage_by_locality(
    calibration: Iterable[Grouped],
    held_out: Iterable[Grouped],
    *,
    covered: Iterable[bool],
    alpha: float = 0.10,
    confidence: float = 0.95,
) -> CoverageReport:
    """Audit already-constructed prediction sets per held-out locality.

    ``covered`` is aligned with ``held_out`` and is supplied by the prediction-set evaluator;
    this function does not compute mineralogical values.  Calibration and held-out units are
    checked for locality disjointness before any proportion is reported.  The band's honest
    ``n`` is the number of distinct calibration localities, never the number of pixels.
    """
    calibration_units = tuple(calibration)
    held_out_units = tuple(held_out)
    covered_values = tuple(covered)
    if not calibration_units:
        raise ValueError("calibration is empty")
    if not held_out_units:
        raise ValueError("held_out is empty")
    if len(covered_values) != len(held_out_units):
        raise ValueError("covered must have one boolean per held-out unit")
    if any(not isinstance(value, bool) for value in covered_values):
        raise ValueError("covered values must be booleans")

    require_locality_disjoint(calibration_units, held_out_units)
    seen_sections: dict[str, str] = {}
    for unit in (*calibration_units, *held_out_units):
        prior = seen_sections.setdefault(unit.section_id, unit.locality)
        if prior != unit.locality:
            raise ValueError(
                f"section {unit.section_id} is filed under two localities: {prior} and "
                f"{unit.locality}. Fix the manifest before auditing coverage."
            )
    calibration_localities = {unit.locality for unit in calibration_units}
    if len(calibration_localities) < 2:
        raise ValueError("calibration must contain at least two independent localities")

    band = coverage_band(
        len(calibration_localities),
        alpha=alpha,
        confidence=confidence,
    )
    by_locality: dict[str, list[bool]] = defaultdict(list)
    for unit, is_covered in zip(held_out_units, covered_values, strict=True):
        by_locality[unit.locality].append(is_covered)

    results = tuple(
        LocalityCoverage(
            locality=locality,
            n_observations=len(values),
            n_covered=sum(values),
            band=band,
        )
        for locality, values in sorted(by_locality.items())
    )
    return CoverageReport(band=band, localities=results)
