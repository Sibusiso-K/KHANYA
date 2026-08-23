"""The conformal coverage figures in `docs/02-gauntlet-findings.md` F3.

F3 originally sized calibration sets from `sqrt(0.9*0.1/n)`, the binomial Wald
standard error. Split-conformal coverage is not binomial: for a calibration set
of size *n* at miscoverage alpha, coverage is Beta(n + 1 - l, l) distributed
with l = floor((n + 1) * alpha) (Vovk 2012; Lei et al. 2018, "Distribution-Free
Predictive Inference for Regression").

The two agree closely at n = 100 and diverge at the small n that a
locality-grouped split actually leaves you with, which is the regime the
finding is about. The Wald form is optimistic there, so sizing from it buys
less coverage precision than it promises.

These tests pin the numbers now quoted in the document. They are not testing
`reefprint` code - they are testing that a claim in the design record still
matches what the arithmetic says, so that the document cannot silently rot.
"""

import math

import pytest
from scipy.stats import beta

TARGET_COVERAGE = 0.90
ALPHA = 1.0 - TARGET_COVERAGE


def conformal_coverage_sd_pp(n_cal: int, alpha: float = ALPHA) -> float:
    """SD of split-conformal coverage, in percentage points.

    Coverage ~ Beta(n + 1 - l, l), l = floor((n + 1) * alpha).
    """
    lower_rank = math.floor((n_cal + 1) * alpha)
    return float(beta(n_cal + 1 - lower_rank, lower_rank).std() * 100.0)


def wald_coverage_sd_pp(n_cal: int, coverage: float = TARGET_COVERAGE) -> float:
    """The binomial Wald SE the finding used to quote. Kept to pin the gap."""
    return math.sqrt(coverage * (1.0 - coverage) / n_cal) * 100.0


def test_conformal_coverage_sd_at_n_100_is_2_96_pp() -> None:
    """F3 quotes 2.96 pp at n_cal = 100."""
    assert conformal_coverage_sd_pp(100) == pytest.approx(2.96, abs=0.005)


def test_conformal_coverage_sd_at_n_20_is_6_26_pp() -> None:
    """F3 quotes 6.26 pp at n_cal = 20, the realistic locality-split size."""
    assert conformal_coverage_sd_pp(20) == pytest.approx(6.26, abs=0.005)


def test_the_wald_form_is_optimistic_and_worst_where_it_matters() -> None:
    """The reason the correction is worth making, as a number.

    The Wald SE overstates precision at both sizes, and the error grows as n
    falls - which is the direction that matters, because the small n is the
    one an honest locality-grouped split leaves you with.
    """
    error_at_100 = wald_coverage_sd_pp(100) / conformal_coverage_sd_pp(100) - 1.0
    error_at_20 = wald_coverage_sd_pp(20) / conformal_coverage_sd_pp(20) - 1.0

    assert error_at_100 > 0.0, "Wald should overstate precision at n = 100"
    assert error_at_20 > 0.0, "Wald should overstate precision at n = 20"
    assert error_at_20 > error_at_100, (
        f"the Wald error should worsen as n falls: {error_at_20:.1%} at n = 20 "
        f"vs {error_at_100:.1%} at n = 100"
    )
    assert error_at_20 == pytest.approx(0.072, abs=0.001), (
        "F3 quotes the Wald form as running 7.2% high at n = 20"
    )


def test_the_two_r_squared_intervals_overlap_which_is_f3s_point() -> None:
    """R2 = 0.90 and R2 = 0.75 at n = 15 are not distinguishable.

    Fisher z, 95%, r = sqrt(R2) - the convention F3 now states explicitly,
    because the original sentence compared an r-scale bound against R2-scale
    intervals and read as though 0.63 were an R2.
    """
    n_specimens = 15
    se = 1.0 / math.sqrt(n_specimens - 3)

    def fisher_ci_in_r_squared(r_squared: float) -> tuple[float, float]:
        r = math.sqrt(r_squared)
        z = 0.5 * math.log((1.0 + r) / (1.0 - r))
        return (
            math.tanh(z - 1.96 * se) ** 2,
            math.tanh(z + 1.96 * se) ** 2,
        )

    high_lo, high_hi = fisher_ci_in_r_squared(0.90)
    low_lo, low_hi = fisher_ci_in_r_squared(0.75)

    assert (high_lo, high_hi) == (pytest.approx(0.72, abs=0.005), pytest.approx(0.97, abs=0.005))
    assert (low_lo, low_hi) == (pytest.approx(0.40, abs=0.005), pytest.approx(0.91, abs=0.005))

    overlap_lo, overlap_hi = max(high_lo, low_lo), min(high_hi, low_hi)
    assert overlap_hi > overlap_lo, "the intervals must overlap for F3's claim to hold"
    assert (overlap_lo, overlap_hi) == (
        pytest.approx(0.72, abs=0.005),
        pytest.approx(0.91, abs=0.005),
    )
