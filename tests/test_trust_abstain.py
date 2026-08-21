"""Rule 5, made structural: a conservative default with a stated reason, never "unknown".

Rule 5 is the only one of the four silent-failure rules whose failure moves a plant. Rules 1, 2
and 3 corrupt a *report*; this one corrupts an *action*. And it fails at the worst possible
moment, which is not incidental but structural — gauntlet blind spot 1: novel texture trips the
OOD gate, and novel texture **is** an ore transition. Refusals correlate positively with the
moments that matter.

The submitted abstract says the system "abstains and holds the last-known-good setpoint". That is
the thing this module exists to make impossible. At an ore transition the last-known-good
setpoint is the *most* stale number available, and holding it is the worst action on the menu.
"""

from __future__ import annotations

import re
from dataclasses import fields

import pytest

from reefprint.quantity import assumed, cited, design_target, measured, stipulated
from reefprint.trust.abstain import (
    Abstention,
    AbstentionTrigger,
    Conservatism,
    ConservativeDefault,
    Prediction,
    audit_abstentions,
    value_to_act_on,
)

# --------------------------------------------------------------------------------------
# Helpers: one head, declared once, the way a real head would declare itself
# --------------------------------------------------------------------------------------


def entrainment_risk_default() -> ConservativeDefault:
    """Fine-chromite entrainment risk, dimensionless in [0, 1]. High risk is the safe guess."""
    return ConservativeDefault(
        applies_to="fine-chromite entrainment risk",
        quantity=assumed(0.90, "", "conservative default: treat an abstention as high risk"),
        direction=Conservatism.ASSUME_HIGH,
        low=stipulated(0.0, "", "entrainment risk index is in [0, 1] by construction"),
        high=stipulated(1.0, "", "entrainment risk index is in [0, 1] by construction"),
    )


# --------------------------------------------------------------------------------------
# "Conservative" is meaningless until you say which way the harm lies
# --------------------------------------------------------------------------------------


def test_a_conservative_default_declares_which_direction_is_safe():
    default = entrainment_risk_default()

    assert default.direction is Conservatism.ASSUME_HIGH


def test_a_default_on_the_unsafe_side_is_refused():
    """The inversion. It says *assume high risk* and then emits the lowest risk there is.

    This is the silent failure rule 5 is really about: the declaration and the number disagree,
    the code runs, and the plant is told there is nothing to worry about at a transition.
    """
    with pytest.raises(ValueError, match="ASSUME_HIGH"):
        ConservativeDefault(
            applies_to="fine-chromite entrainment risk",
            quantity=assumed(0.05, "", "a default someone thought was cautious"),
            direction=Conservatism.ASSUME_HIGH,
            low=stipulated(0.0, "", "index range"),
            high=stipulated(1.0, "", "index range"),
        )


def test_the_inversion_is_refused_in_the_other_direction_too():
    """A recovery estimate: low is safe. A default near the top is the same bug, mirrored."""
    with pytest.raises(ValueError, match="ASSUME_LOW"):
        ConservativeDefault(
            applies_to="PGE recovery",
            quantity=assumed(95.0, "percent", "optimistic default"),
            direction=Conservatism.ASSUME_LOW,
            low=stipulated(0.0, "percent", "recovery is a percentage"),
            high=stipulated(100.0, "percent", "recovery is a percentage"),
        )


def test_a_default_at_the_conservative_extreme_is_accepted():
    default = ConservativeDefault(
        applies_to="fine-chromite entrainment risk",
        quantity=assumed(1.0, "", "maximum risk on abstention"),
        direction=Conservatism.ASSUME_HIGH,
        low=stipulated(0.0, "", "index range"),
        high=stipulated(1.0, "", "index range"),
    )

    assert default.quantity.value == pytest.approx(1.0)


def test_a_default_outside_its_own_declared_range_is_refused():
    with pytest.raises(ValueError, match="outside"):
        ConservativeDefault(
            applies_to="fine-chromite entrainment risk",
            quantity=assumed(1.4, "", "a risk index above 1"),
            direction=Conservatism.ASSUME_HIGH,
            low=stipulated(0.0, "", "index range"),
            high=stipulated(1.0, "", "index range"),
        )


def test_an_inverted_range_is_refused():
    with pytest.raises(ValueError, match="range"):
        ConservativeDefault(
            applies_to="fine-chromite entrainment risk",
            quantity=assumed(0.9, "", "high risk"),
            direction=Conservatism.ASSUME_HIGH,
            low=stipulated(1.0, "", "swapped"),
            high=stipulated(0.0, "", "swapped"),
        )


def test_a_zero_width_range_is_refused_because_there_is_nothing_to_be_conservative_about():
    with pytest.raises(ValueError, match="range"):
        ConservativeDefault(
            applies_to="a head with one possible answer",
            quantity=assumed(0.5, "", "the only value"),
            direction=Conservatism.ASSUME_HIGH,
            low=stipulated(0.5, "", "degenerate"),
            high=stipulated(0.5, "", "degenerate"),
        )


def test_units_must_agree_across_the_default_and_its_range():
    """A default in percent against a range in fractions is off by a hundred, silently."""
    with pytest.raises(ValueError, match="unit"):
        ConservativeDefault(
            applies_to="PGE recovery",
            quantity=assumed(90.0, "percent", "conservative default"),
            direction=Conservatism.ASSUME_LOW,
            low=stipulated(0.0, "", "fraction, not percent"),
            high=stipulated(1.0, "", "fraction, not percent"),
        )


# --------------------------------------------------------------------------------------
# The rule 1 seam: a conservative default is a number, so it cannot be invented
# --------------------------------------------------------------------------------------


def test_a_default_derived_from_the_design_target_is_refused():
    """Where rule 5 meets rule 1. A control value from hardware that was never built."""
    with pytest.raises(ValueError, match="ADR-0002"):
        ConservativeDefault(
            applies_to="grain size cutoff",
            quantity=design_target(1.6, "um/px", "CLAUDE.md design target"),
            direction=Conservatism.ASSUME_HIGH,
            low=stipulated(0.0, "um/px", "range"),
            high=stipulated(2.0, "um/px", "range"),
        )


def test_a_cited_plant_limit_is_an_acceptable_default():
    """Most real conservative defaults are plant facts, not measurements. Cited is enough."""
    default = ConservativeDefault(
        applies_to="depressant dose",
        quantity=cited(250.0, "g/t", "plant maximum depressant dose, standard operating limit"),
        direction=Conservatism.ASSUME_HIGH,
        low=cited(0.0, "g/t", "no dosing"),
        high=cited(300.0, "g/t", "reagent system maximum"),
    )

    assert "plant maximum depressant dose" in default.quantity.cite()


def test_the_defaults_provenance_survives_being_emitted():
    """The number that reaches the controller still says it is an assumption."""
    abstention = Abstention(
        default=entrainment_risk_default(),
        reason="feature vector is outside the convex hull of the training localities",
        trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
    )

    assert "assumption" in abstention.emit().cite().lower()


# --------------------------------------------------------------------------------------
# Never "unknown"
# --------------------------------------------------------------------------------------


def test_an_abstention_must_state_a_reason():
    with pytest.raises(ValueError, match="reason"):
        Abstention(
            default=entrainment_risk_default(),
            reason="",
            trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
        )


def test_the_reason_unknown_is_refused_because_the_rule_names_it():
    """Rule 5 forbids the word. It is the one non-reason common enough to name."""
    with pytest.raises(ValueError, match="unknown"):
        Abstention(
            default=entrainment_risk_default(),
            reason="unknown",
            trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
        )


@pytest.mark.parametrize("non_reason", ["Unknown", "  UNKNOWN  ", "n/a", "N/A", "?", "none"])
def test_the_usual_non_reasons_are_refused_however_they_are_spelled(non_reason):
    with pytest.raises(ValueError, match="not a reason"):
        Abstention(
            default=entrainment_risk_default(),
            reason=non_reason,
            trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
        )


def test_a_real_reason_is_accepted_and_kept_verbatim():
    reason = "conformal set spans chromite and pentlandite; the split governs PGE deportment"
    abstention = Abstention(
        default=entrainment_risk_default(),
        reason=reason,
        trigger=AbstentionTrigger.CONFORMAL_SET_TOO_WIDE,
    )

    assert abstention.reason == reason


def test_the_explanation_carries_both_the_trigger_and_the_reason():
    """An operator gets one line. It has to say what fired and what is being done instead."""
    abstention = Abstention(
        default=entrainment_risk_default(),
        reason="polish quality gate failed: relief at the sulphide-silicate boundary",
        trigger=AbstentionTrigger.DEGRADED_INPUT,
    )

    explanation = abstention.explain()

    assert "relief at the sulphide-silicate boundary" in explanation
    assert "quality gate" in explanation.lower()
    assert "0.9" in explanation


# --------------------------------------------------------------------------------------
# The abstract's contradiction, as a test
# --------------------------------------------------------------------------------------


def test_an_abstention_emits_the_conservative_default_not_the_previous_prediction():
    """The submitted abstract says "holds the last-known-good setpoint". This refutes it.

    Steady state reads low risk; then the ore changes, the gate fires, and the question is what
    reaches the controller. Holding 0.12 is the abstract's answer and the dangerous one.
    """
    steady = Prediction(
        head="fine-chromite entrainment risk",
        quantity=measured(0.12, "", "bridge/measure.py, stable feed"),
    )
    transition = Abstention(
        default=entrainment_risk_default(),
        reason="texture is unlike any training locality; likely an ore transition",
        trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
    )

    assert value_to_act_on(steady).value == pytest.approx(0.12)
    assert value_to_act_on(transition).value == pytest.approx(0.90)


def test_an_abstention_cannot_carry_a_previous_value_to_hold():
    """Structural, not behavioural: there is no field for the last setpoint, so it cannot hold.

    A behavioural test proves today's code does the right thing. This one is what stops someone
    adding ``previous=`` in six weeks because a demo looked jumpy.
    """
    assert {f.name for f in fields(Abstention)} == {"default", "reason", "trigger"}


def test_acting_on_a_decision_never_yields_nothing():
    """Rule 5's floor. Not None, not a string, not a sentinel. A number with a unit."""
    for decision in (
        Prediction(head="risk", quantity=measured(0.12, "", "a source")),
        Abstention(
            default=entrainment_risk_default(),
            reason="the rotation series is a stage rotation, not a rotating analyser",
            trigger=AbstentionTrigger.UNSUPPORTED_GEOMETRY,
        ),
    ):
        acted_on = value_to_act_on(decision)

        assert acted_on.value is not None
        assert isinstance(acted_on.unit, str)


# --------------------------------------------------------------------------------------
# Blind spot 1: the aggregate rate hides the only conditional that matters
# --------------------------------------------------------------------------------------


def _decisions(pattern: str) -> list[Prediction | Abstention]:
    """``a`` for abstention, ``p`` for prediction. Reads as the timeline it represents."""
    made = []
    for char in pattern:
        if char == "a":
            made.append(
                Abstention(
                    default=entrainment_risk_default(),
                    reason="texture outside the training distribution",
                    trigger=AbstentionTrigger.OUT_OF_DISTRIBUTION,
                )
            )
        else:
            made.append(Prediction(head="risk", quantity=measured(0.12, "", "a source")))
    return made


def test_an_audit_with_no_ore_change_events_is_refused():
    """The only conditional that matters cannot be computed, so the aggregate would be quoted.

    Which is the flattering error: 4% overall reads as a well-behaved gate, and says nothing
    about the transitions, because there were none to say anything about.
    """
    with pytest.raises(ValueError, match="ore-change"):
        audit_abstentions(_decisions("ppppap"), ore_change=[False] * 6)


def test_an_empty_audit_is_refused():
    with pytest.raises(ValueError, match="empty"):
        audit_abstentions([], ore_change=[])


def test_mismatched_lengths_are_refused():
    with pytest.raises(ValueError, match="length"):
        audit_abstentions(_decisions("ppp"), ore_change=[False, True])


def test_the_conditional_rate_can_be_far_worse_than_the_aggregate():
    """Blind spot 1, in numbers. Sixteen frames, two of them transitions, both abstained."""
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert audit.rate_overall == pytest.approx(2 / 15)
    assert audit.rate_during_ore_change == pytest.approx(1.0)
    assert audit.rate_when_stable == pytest.approx(0.0)


def test_the_summary_never_reports_the_aggregate_alone():
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    summary = audit.summary()

    assert "ore change" in summary.lower()
    assert "stable" in summary.lower()


def test_abstention_concentrated_at_transitions_is_flagged_in_words():
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert audit.concentrates_at_transitions
    assert "blind spot 1" in audit.summary().lower()


def test_abstention_that_does_not_concentrate_is_not_flagged():
    """The guard has to be able to say the gate is behaving, or it says nothing at all."""
    audit = audit_abstentions(
        _decisions("apapapap"),
        ore_change=[False, False, True, True, False, False, True, True],
    )

    assert not audit.concentrates_at_transitions


def test_a_higher_conditional_rate_at_small_n_is_not_flagged_as_concentrating():
    """A plain rate comparison used to be the whole test, and it fired on point estimates alone.

    1/3 during ore change vs 5/20 stable is a higher rate — and Fisher's exact test on that
    table (p ≈ 0.62) says it is nowhere near distinguishable from noise. The old code had no
    way to say that; it just compared 0.333 to 0.250 and called it concentration.
    """
    audit = audit_abstentions(
        _decisions("app" + "aaaaa" + "p" * 15),
        ore_change=[True, True, True] + [False] * 20,
    )

    assert audit.rate_during_ore_change > audit.rate_when_stable
    assert not audit.concentrates_at_transitions


def test_the_canonical_concentration_example_is_backed_by_a_real_test():
    """The two-event example is exactly where the old rate comparison was least trustworthy.

    Fisher's exact test does not degenerate the way the Wald SE does — it resolves this table
    (p ≈ 0.0095) even though :attr:`bound_during_ore_change` can only say the rate itself
    "resolves nothing" at n = 2. The comparison and the rate are different questions.
    """
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert audit.concentrates_at_transitions
    assert audit.concentration_p_value is not None
    assert audit.concentration_p_value < 0.05
    assert "fisher" in audit.summary().lower()


def test_concentration_cannot_be_assessed_with_no_stable_frames():
    """Every frame was a transition — there is no baseline to compare against, not a 0% one."""
    audit = audit_abstentions(
        _decisions("aap"),
        ore_change=[True, True, True],
    )

    assert audit.n_stable == 0
    assert audit.concentration_p_value is None
    assert not audit.concentrates_at_transitions


def test_an_elevated_but_unresolved_rate_is_not_reported_as_either_verdict():
    """Neither "blind spot 1" (overclaims a real finding) nor "do not concentrate" (overclaims
    safety) is honest here — the summary has to say the comparison is unresolved.
    """
    audit = audit_abstentions(
        _decisions("app" + "aaaaa" + "p" * 15),
        ore_change=[True, True, True] + [False] * 20,
    )

    summary = audit.summary().lower()

    assert "blind spot 1" not in summary
    assert "do not concentrate" not in summary


def test_the_conditional_rate_carries_its_own_honest_n():
    """Rule 4. Honest n for the conditional is the number of ore-change events, not of frames."""
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert audit.n_ore_change == 2
    assert audit.n_stable == 13


def test_a_conditional_rate_on_two_events_is_reported_as_the_noise_it_is():
    """Two transitions resolve almost nothing, and the line has to say so rather than imply 100%."""
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert "n = 2" in audit.summary()


def test_the_noise_on_a_rate_uses_the_same_arithmetic_as_the_rest_of_the_package():
    """sqrt(p(1-p)/n), not a threshold invented here. Rule 1 applies to guards too."""
    audit = audit_abstentions(
        _decisions("papa"),
        ore_change=[False, False, True, True],
    )

    assert audit.noise_during_ore_change == pytest.approx((0.5 * 0.5 / 2) ** 0.5)


def test_the_audit_counts_abstentions_not_frames():
    audit = audit_abstentions(
        _decisions("aappp"),
        ore_change=[True, True, False, False, False],
    )

    assert audit.n_abstentions == 2
    assert audit.n_decisions == 5


# --------------------------------------------------------------------------------------
# The escape hatch, and why it is narrow
# --------------------------------------------------------------------------------------


def test_the_position_in_range_is_reported_so_a_reviewer_can_judge_how_far():
    """The guard refuses the wrong *side*. How far along is domain judgement, so it is shown.

    Enforcing a distance would mean inventing a threshold, and a default pinned to the extreme
    makes operators switch the system off, which is worse than a default that is merely timid.
    """
    default = entrainment_risk_default()

    assert default.position_in_range == pytest.approx(0.90)
    assert re.search(r"90(\.0)?%", default.explain())


def test_the_explanation_names_the_head_it_applies_to():
    assert "fine-chromite entrainment risk" in entrainment_risk_default().explain()


# --------------------------------------------------------------------------------------
# The degenerate end of the binomial, which is where small n actually lands
# --------------------------------------------------------------------------------------


def test_a_rate_of_one_is_not_reported_as_perfectly_precise():
    """sqrt(p(1-p)/n) is exactly 0 at p = 1, so two-for-two prints as certainty.

    That is an invented number in the most literal sense: the arithmetic returns a precision
    the data cannot support, and it is the extreme observations - the ones small runs actually
    produce - that trigger it.
    """
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    assert audit.noise_during_ore_change is None


def test_two_events_that_all_abstained_do_not_print_a_plus_minus_zero():
    audit = audit_abstentions(
        _decisions("pppppppaapppppp"),
        ore_change=[False] * 7 + [True, True] + [False] * 6,
    )

    summary = audit.summary()
    conditional = summary.split("during ore change (")[1].split(")")[0]

    assert "0.0%" not in conditional
    assert "resolves nothing" in conditional


def test_the_rule_of_three_is_used_where_it_actually_bounds_something():
    """Ten transitions, all abstained. 3/n gives a 95% lower bound of 70%, which is a statement."""
    audit = audit_abstentions(
        _decisions("a" * 10 + "p" * 10),
        ore_change=[True] * 10 + [False] * 10,
    )

    assert audit.noise_during_ore_change is None
    assert "70" in audit.summary()


def test_a_rate_of_zero_at_the_transitions_is_bounded_the_same_way():
    """The good news case has the same defect: 0 of 10 is not proof the gate never fires."""
    audit = audit_abstentions(
        _decisions("p" * 10 + "a" * 10),
        ore_change=[True] * 10 + [False] * 10,
    )

    assert audit.rate_during_ore_change == pytest.approx(0.0)
    assert "30" in audit.summary()
