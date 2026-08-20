"""Rule 3, made structural: report the trivial baseline alongside every metric. Always.

"Always" is the load-bearing word, and prose cannot enforce it — the omission is invisible in
the output. A metric reported without its baselines looks exactly like a metric reported with
them, minus the one number that says whether it means anything. So the baselines are a required
field: a bare metric is not constructable.
"""

from __future__ import annotations

import pytest

from reefprint.trust.baseline import (
    NotApplicable,
    ScoredMetric,
    TrivialBaselines,
    majority_class_rate,
)


def baselines(majority: float = 0.50, metadata: float | NotApplicable = 0.60) -> TrivialBaselines:
    return TrivialBaselines(majority_class=majority, metadata_only=metadata)


# --------------------------------------------------------------------------------------
# The metric cannot exist without them
# --------------------------------------------------------------------------------------


def test_a_metric_cannot_be_constructed_without_its_baselines():
    """Rule 3 as a TypeError. No default, so forgetting is not an available mistake."""
    with pytest.raises(TypeError):
        ScoredMetric(name="balanced accuracy", value=0.81, n=12)  # type: ignore[call-arg]


def test_a_metric_with_baselines_constructs():
    metric = ScoredMetric(name="balanced accuracy", value=0.81, n=12, baselines=baselines())

    assert metric.value == pytest.approx(0.81)


# --------------------------------------------------------------------------------------
# And it cannot be reported without naming them
# --------------------------------------------------------------------------------------


def test_the_summary_names_every_baseline():
    metric = ScoredMetric(name="balanced accuracy", value=0.81, n=12, baselines=baselines())

    summary = metric.summary()

    assert "majority class" in summary
    assert "metadata-only" in summary
    assert "0.81" in summary


def test_a_metric_below_its_baseline_says_so_in_words():
    """Nobody reading a slide subtracts two numbers. The summary has to do it for them."""
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.55,
        n=12,
        baselines=baselines(majority=0.50, metadata=0.60),
    )

    assert "does not beat" in metric.summary().lower()


def test_an_uplift_smaller_than_the_noise_at_honest_n_is_named_as_such():
    """The case rule 3 exists for, and the one rule 4 finishes.

    0.62 next to a 0.60 baseline reads as a result. At n = 12 the standard error on a
    proportion near 0.6 is sqrt(0.6 * 0.4 / 12) ≈ 0.14, so a +0.02 uplift is a seventh of
    one standard error. Positive, so "does not beat" would be false; meaningless, so silence
    would be worse. The summary has to say which.

    The formula is the one the package already quotes for conformal coverage SD — not a
    threshold invented here (rule 1).
    """
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.62,
        n=12,
        baselines=baselines(majority=0.50, metadata=0.60),
    )

    assert metric.uplift == pytest.approx(0.02)
    assert not metric.uplift_exceeds_noise
    assert "n = 12 resolves" in metric.summary()


def test_an_uplift_larger_than_the_noise_is_reported_as_an_uplift():
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.92,
        n=40,
        baselines=baselines(majority=0.50, metadata=0.60),
    )

    assert metric.uplift_exceeds_noise
    assert "over the strongest baseline" in metric.summary()


def test_noise_is_not_estimated_for_a_metric_that_is_not_a_proportion():
    """A binomial standard error on an RMSE or an R² is an invented number. Rule 1.

    The verdict falls back to the plain uplift rather than quoting an SE that does not apply.
    """
    metric = ScoredMetric(
        name="grain-size RMSE (um)",
        value=4.2,
        n=12,
        baselines=TrivialBaselines(majority_class=9.0, metadata_only=7.5),
    )

    assert metric.noise_at_honest_n is None
    assert "resolves" not in metric.summary()


def test_uplift_is_measured_against_the_strongest_baseline_not_the_weakest():
    """Quoting the gap to majority class when metadata-only is stronger is the flattering error.

    0.62 vs the 0.50 majority class is +0.12 and sounds like a contribution. Against the 0.60
    metadata-only baseline it is +0.02, which is the honest number.
    """
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.62,
        n=12,
        baselines=baselines(majority=0.50, metadata=0.60),
    )

    assert metric.uplift == pytest.approx(0.02)
    assert metric.strongest_baseline == pytest.approx(0.60)


def test_uplift_is_negative_when_the_baseline_wins():
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.55,
        n=12,
        baselines=baselines(majority=0.50, metadata=0.60),
    )

    assert metric.uplift == pytest.approx(-0.05)
    assert not metric.beats_baseline


# --------------------------------------------------------------------------------------
# Omitting one is allowed, silently omitting one is not
# --------------------------------------------------------------------------------------


def test_a_baseline_may_be_not_applicable_but_only_with_a_stated_reason():
    """Mirrors rule 5: the escape hatch emits a reason, never "unknown"."""
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.81,
        n=12,
        baselines=baselines(metadata=NotApplicable("LumenStone ships no per-section metadata")),
    )

    summary = metric.summary()

    assert "LumenStone ships no per-section metadata" in summary


def test_not_applicable_without_a_reason_is_refused():
    with pytest.raises(ValueError, match="reason"):
        NotApplicable("")


def test_a_not_applicable_baseline_does_not_count_towards_the_strongest():
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.62,
        n=12,
        baselines=baselines(majority=0.50, metadata=NotApplicable("no metadata")),
    )

    assert metric.strongest_baseline == pytest.approx(0.50)
    assert metric.uplift == pytest.approx(0.12)


def test_both_baselines_not_applicable_is_refused():
    """At that point there is no baseline at all, which is the state rule 3 forbids."""
    with pytest.raises(ValueError, match="at least one"):
        TrivialBaselines(
            majority_class=NotApplicable("single class"),
            metadata_only=NotApplicable("no metadata"),
        )


# --------------------------------------------------------------------------------------
# The majority-class rate itself
# --------------------------------------------------------------------------------------


def test_majority_class_rate_is_the_modal_frequency():
    labels = ("pn", "pn", "pn", "po", "po", "ccp", "chr", "chr")

    assert majority_class_rate(labels) == pytest.approx(3 / 8)


def test_majority_class_rate_of_a_single_class_is_one():
    assert majority_class_rate(("pn", "pn", "pn")) == pytest.approx(1.0)


def test_majority_class_rate_of_nothing_is_refused():
    with pytest.raises(ValueError, match="empty"):
        majority_class_rate(())


# --------------------------------------------------------------------------------------
# Rule 4 rides along
# --------------------------------------------------------------------------------------


def test_the_summary_carries_the_honest_n():
    """A metric without n cannot carry a CI, and rule 4 says every metric carries one."""
    metric = ScoredMetric(name="balanced accuracy", value=0.81, n=12, baselines=baselines())

    assert "n = 12" in metric.summary()


def test_a_metric_with_no_n_is_refused():
    with pytest.raises(ValueError, match="n"):
        ScoredMetric(name="balanced accuracy", value=0.81, n=0, baselines=baselines())
