"""Cluster bootstrap CIs and the paired exact test — the tools the plan specified for Workstream
D and never built, applied for real the first time to `khanya/main`'s decision-gap evidence
(`experiments/013-decision-gap-refinement-sensitivity/`).
"""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.trust.bootstrap import cluster_bootstrap_ci, paired_exact_test

# --------------------------------------------------------------------------------------
# cluster_bootstrap_ci
# --------------------------------------------------------------------------------------


def test_bootstrap_ci_is_deterministic_given_the_same_seed():
    """Rule 5: the same seed must return bit-for-bit the same interval, not merely a similar one
    — exactly the property `experiments/010`'s grid search turned out to lack.
    """
    values = [0.1, 0.4, 0.6, 0.9, 0.2, 0.7]
    first = cluster_bootstrap_ci(values, rng=np.random.default_rng(0))
    second = cluster_bootstrap_ci(values, rng=np.random.default_rng(0))

    assert first == second


def test_bootstrap_ci_differs_across_seeds_but_stays_close():
    """A sanity check that the seed is actually consulted, not silently ignored."""
    values = [0.1, 0.4, 0.6, 0.9, 0.2, 0.7]
    first = cluster_bootstrap_ci(values, rng=np.random.default_rng(0))
    second = cluster_bootstrap_ci(values, rng=np.random.default_rng(1))

    assert (first.low, first.high) != (second.low, second.high)
    assert first.point_estimate == second.point_estimate == pytest.approx(np.mean(values))


def test_bootstrap_ci_contains_the_point_estimate():
    values = [0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.3, 0.7]
    result = cluster_bootstrap_ci(values, rng=np.random.default_rng(42), n_resamples=2000)

    assert result.low <= result.point_estimate <= result.high


def test_bootstrap_ci_widens_with_fewer_units():
    """The whole point of Rule 2's cluster discipline: an interval built from few independent
    units must be wide, not falsely tight — resampling individual pixels inside those units
    would hide exactly this.
    """
    rng = np.random.default_rng(7)
    many_units = list(rng.uniform(0.3, 0.7, size=200))
    few_units = many_units[:5]

    wide = cluster_bootstrap_ci(few_units, rng=np.random.default_rng(0))
    narrow = cluster_bootstrap_ci(many_units, rng=np.random.default_rng(0))

    assert (wide.high - wide.low) > (narrow.high - narrow.low)


def test_bootstrap_ci_reports_the_honest_n():
    values = [0.1, 0.2, 0.3, 0.4, 0.5]
    result = cluster_bootstrap_ci(values, rng=np.random.default_rng(0))

    assert result.n_units == 5
    assert "n = 5 clusters" in result.describe()


@pytest.mark.parametrize("bad_values", [[], [0.5]])
def test_bootstrap_ci_refuses_fewer_than_two_units(bad_values):
    with pytest.raises(ValueError, match="at least 2"):
        cluster_bootstrap_ci(bad_values, rng=np.random.default_rng(0))


@pytest.mark.parametrize("bad_confidence", [0.0, 1.0, -0.1, 1.5])
def test_bootstrap_ci_refuses_a_confidence_outside_zero_one(bad_confidence):
    with pytest.raises(ValueError, match="confidence"):
        cluster_bootstrap_ci(
            [0.1, 0.2, 0.3], confidence=bad_confidence, rng=np.random.default_rng(0)
        )


def test_bootstrap_ci_refuses_zero_resamples():
    with pytest.raises(ValueError, match="n_resamples"):
        cluster_bootstrap_ci([0.1, 0.2, 0.3], n_resamples=0, rng=np.random.default_rng(0))


def test_bootstrap_ci_accepts_a_custom_statistic():
    """The flip-rate use case this module was built for: a mean over a 0/1-coded sequence, but
    the same machinery works for any per-unit statistic.
    """
    flips = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0]  # 3 of 6 units flipped
    result = cluster_bootstrap_ci(flips, rng=np.random.default_rng(0))

    assert result.point_estimate == pytest.approx(0.5)


# --------------------------------------------------------------------------------------
# paired_exact_test
# --------------------------------------------------------------------------------------


def test_paired_exact_test_refuses_mismatched_units():
    a = {"s1": True, "s2": False}
    b = {"s1": True, "s3": False}
    with pytest.raises(ValueError, match="same units"):
        paired_exact_test(a, b)


def test_paired_exact_test_perfect_agreement_gives_p_one():
    a = {"s1": True, "s2": False, "s3": True}
    b = {"s1": True, "s2": False, "s3": True}
    result = paired_exact_test(a, b)

    assert result.n_discordant == 0
    assert result.p_value == 1.0
    assert not result.significant_at_05


def test_paired_exact_test_balanced_disagreement_is_not_significant():
    """The exact case this module exists for: `experiments/013`'s finding that raw and refined
    decision-gap conditions flip a *different* pair of sections each (2 vs 2) while agreeing on
    the other four. A perfectly balanced discordant split is precisely what the null predicts —
    p must come out at 1.0, not some smaller number that would misleadingly suggest evidence of
    a difference.
    """
    a = {f"s{i}": (i in (1, 2, 5, 6)) for i in range(1, 9)}  # flips: 1,2,5,6
    b = {f"s{i}": (i in (1, 2, 7, 8)) for i in range(1, 9)}  # flips: 1,2,7,8 -> discordant 5,6,7,8
    result = paired_exact_test(a, b)

    assert result.n_discordant == 4
    assert set(result.only_in_a) == {"s5", "s6"}
    assert set(result.only_in_b) == {"s7", "s8"}
    assert result.p_value == pytest.approx(1.0)
    assert not result.significant_at_05


def test_paired_exact_test_lopsided_disagreement_is_significant():
    """A known reference case: 10 discordant pairs split 9-vs-1 gives an exact two-sided
    p-value of approximately 0.0215 (the standard textbook McNemar/exact-binomial-sign-test
    example).
    """
    a = {f"s{i}": True for i in range(9)}
    b = {f"s{i}": False for i in range(9)}
    a["s9"] = False
    b["s9"] = True

    result = paired_exact_test(a, b)

    assert result.n_discordant == 10
    assert len(result.only_in_a) == 9
    assert len(result.only_in_b) == 1
    assert result.p_value == pytest.approx(0.02148, abs=1e-4)
    assert result.significant_at_05


def test_paired_exact_test_low_power_note_appears_for_small_discordant_counts():
    a = {"s1": True, "s2": False, "s3": True, "s4": False}
    b = {"s1": False, "s2": True, "s3": True, "s4": False}
    result = paired_exact_test(a, b)

    assert result.n_discordant == 2
    assert "negligible power" in result.describe()
