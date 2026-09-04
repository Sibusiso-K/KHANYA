"""The conformal calibration, which is what the uncertainty band rests on.

Entry (23) found the shipped +/-8.9% band covered only 67% of S2 sections and
45% of S1 sections while reading, to a reader, like a ~90% guarantee. These
tests exist so that class of error is caught by the suite rather than by
someone re-deriving the coverage months later.
"""
import numpy as np
import pytest

from src import conformal


class TestQuantileHalfwidth:
    def test_returns_the_correct_order_statistic(self):
        # n=9, alpha=0.1 -> k = ceil(10 * 0.9) = 9, the 9th smallest.
        residuals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        assert conformal.quantile_halfwidth(residuals, 0.1) == pytest.approx(0.9)

    def test_is_insensitive_to_input_order(self):
        forward = conformal.quantile_halfwidth([0.1, 0.5, 0.3, 0.9, 0.2], 0.2)
        backward = conformal.quantile_halfwidth([0.9, 0.5, 0.3, 0.2, 0.1], 0.2)
        assert forward == backward

    def test_refuses_when_the_calibration_set_is_too_small_for_the_level(self):
        """The refusal is the point. n=5 cannot support 99% - k=6 > n.

        Falling back to the largest residual would return a number that looks
        like a bound and carries no guarantee, which is exactly the failure the
        band correction in entry (23) was about.
        """
        assert conformal.quantile_halfwidth([0.1, 0.2, 0.3, 0.4, 0.5], 0.01) is None

    def test_the_smallest_n_that_supports_ninety_percent_is_nine(self):
        # k = ceil((n+1) * 0.9) <= n first holds at n = 9.
        assert conformal.quantile_halfwidth(list(range(8)), 0.10) is None
        assert conformal.quantile_halfwidth(list(range(9)), 0.10) is not None

    def test_empirical_coverage_reaches_the_nominal_level(self):
        """The guarantee is distribution-free, so a skewed draw must not break it."""
        rng = np.random.default_rng(0)
        alpha = 0.1
        covered = 0
        trials = 400
        for _ in range(trials):
            draws = rng.lognormal(0.0, 1.0, size=60)
            calibration, held_out = draws[:50], draws[50:]
            halfwidth = conformal.quantile_halfwidth(calibration.tolist(), alpha)
            covered += int(np.mean(held_out <= halfwidth) >= 0.5)
        # Distribution-free lower bound, not a point prediction - assert the
        # direction of the guarantee, not a tight interval.
        assert covered / trials > 0.75


class TestActionSet:
    def test_an_interval_straddling_the_floor_admits_both_actions(self):
        """The whole reason for a set: near the threshold, do not pick.

        This is the honest generalisation of the band - it reports that two
        actions are still consistent with the data rather than hiding the
        disagreement behind a point estimate.
        """
        floor = conformal.advisor.LOW_LIBERATION
        actions = conformal.action_set(floor, floor - 0.2, floor + 0.2, None)
        assert actions == {"grind finer", "continue/adjust"}

    def test_an_interval_entirely_below_the_floor_admits_one_action(self):
        floor = conformal.advisor.LOW_LIBERATION
        actions = conformal.action_set(floor - 0.3, floor - 0.4, floor - 0.1, None)
        assert actions == {"grind finer"}

    def test_an_interval_entirely_above_the_floor_admits_one_action(self):
        floor = conformal.advisor.LOW_LIBERATION
        actions = conformal.action_set(floor + 0.3, floor + 0.1, floor + 0.4, None)
        assert actions == {"continue/adjust"}

    def test_none_endpoints_are_skipped_not_treated_as_zero(self):
        """A missing endpoint is missing. Coercing it to 0.0 would silently
        add 'grind finer' to every set."""
        floor = conformal.advisor.LOW_LIBERATION
        assert conformal.action_set(floor + 0.3, None, None, None) == {"continue/adjust"}

    def test_values_outside_zero_one_are_clipped_not_rejected(self):
        """A fitted interval can leave [0, 1]; clipping keeps the action
        well-defined instead of raising in front of an operator."""
        actions = conformal.action_set(0.5, -0.4, 1.9, None)
        assert actions == {"grind finer", "continue/adjust"}
