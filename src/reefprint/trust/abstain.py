"""Rule 5, made structural: a conservative default with a stated reason, never "unknown".

Of the four rules that fail silently, this is the only one whose failure moves a plant. Rules 1,
2 and 3 corrupt a *report* — bad, recoverable, embarrassing in front of a judge. Rule 5 corrupts
an *action*.

And it fails at the worst possible moment, which is structural rather than unlucky. Gauntlet
**blind spot 1**: novel texture trips the out-of-distribution gate, and novel texture *is* an ore
transition. Refusals therefore correlate **positively** with the moments that matter. A gate that
abstains 4% of the time overall can be abstaining through every single transition, and the
aggregate number will look excellent.

Three things follow, and all three are enforced here rather than remembered:

**A refusal still emits a number.** :func:`value_to_act_on` returns a
:class:`~reefprint.quantity.Quantity` for a prediction and for an abstention alike. Never
``None``, never the string "unknown", never a sentinel that a downstream ``if`` will quietly skip.
Something is going to reach the controller either way; the only question is whether we chose it.

**The number is not the last one.** The submitted abstract says the system "abstains and holds the
last-known-good setpoint", and that is the specific thing this module makes impossible.
:class:`Abstention` has no field for a previous value and :func:`value_to_act_on` takes no
previous value, so there is nothing to hold. At an ore transition the last-known-good setpoint is
the *most* stale number available. Holding it is not the cautious option; it is the worst action
on the menu, chosen because it looks like caution.

**"Conservative" is meaningless until you say which way the harm lies.** High entrainment risk is
the safe guess; high recovery is not. :class:`ConservativeDefault` requires the direction and the
plausible range, and refuses a default sitting on the unsafe side of that range. That refusal is
the one mechanically detectable form of the bug: a default that *declares* caution and *emits*
the opposite runs perfectly and tells the plant there is nothing to worry about.

How far along the safe side a default should sit is domain judgement, not arithmetic, so it is
reported by :meth:`ConservativeDefault.explain` rather than enforced. Pinning every default to
the extreme is what makes operators switch a system off, and a system that has been switched off
abstains 100% of the time without saying so.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import sqrt

from reefprint.quantity import Quantity, require_reportable

__all__ = [
    "Abstention",
    "AbstentionAudit",
    "AbstentionTrigger",
    "Conservatism",
    "ConservativeDefault",
    "Decision",
    "Prediction",
    "audit_abstentions",
    "value_to_act_on",
]

_NON_REASONS = frozenset({"unknown", "n/a", "na", "none", "error", "tbd", "?", "-", "--"})


class Conservatism(StrEnum):
    """Which end of a head's range is the safe place to be when we do not know.

    There is no default and no inference. Entrainment risk and naturally-floating-gangue load are
    ``ASSUME_HIGH`` — over-dose the depressant, cut the feed, lose a little recovery. Recovery and
    grade are ``ASSUME_LOW``. Getting this backwards produces a system that reassures a plant at
    exactly the moment it should be warning it, and nothing in the output looks wrong.
    """

    ASSUME_HIGH = "assume the high end of the range"
    ASSUME_LOW = "assume the low end of the range"


class AbstentionTrigger(StrEnum):
    """What fired the refusal. The operator's first question, so it is a field, not a guess.

    The wording is the wording that reaches the screen — one place to disagree is one too many.
    """

    OUT_OF_DISTRIBUTION = "the input is outside the training distribution"
    CONFORMAL_SET_TOO_WIDE = "the conformal prediction set is too wide to act on"
    DEGRADED_INPUT = "the image failed a quality gate"
    UNSUPPORTED_GEOMETRY = "the rotation geometry is not a rotating-analyser series"


@dataclass(frozen=True, slots=True)
class ConservativeDefault:
    """The number a head emits when it refuses to answer, and the direction that makes it safe.

    Declared once per head, not per call, which is why it can afford to be expensive to assert.
    A number that moves a plant should be.

    :param quantity: the default itself. A :class:`~reefprint.quantity.Quantity`, so rule 1
        applies: it carries its provenance and it cannot have been invented. Usually ``CITED``
        (a plant operating limit) or ``ASSUMED`` (a stated engineering judgement). Never
        ``DESIGN_TARGET`` — see :func:`~reefprint.quantity.require_reportable`.
    :param direction: which end of ``[low, high]`` is safe. No default; see :class:`Conservatism`.
    :param low: bottom of the head's plausible range.
    :param high: top of it. Same unit as ``quantity``, checked.

    :raises ValueError: if the units disagree, the range is empty or inverted, the default falls
        outside its own range, the default derives from a design target, or the default sits on
        the **unsafe** side of the range's midpoint.
    """

    applies_to: str
    quantity: Quantity
    direction: Conservatism
    low: Quantity
    high: Quantity

    def __post_init__(self) -> None:
        units = {self.quantity.unit, self.low.unit, self.high.unit}
        if len(units) != 1:
            raise ValueError(
                f"{self.applies_to}: the default and its range must share a unit, got "
                f"{sorted(units)!r}. A default in percent against a range in fractions is off "
                "by a hundred and nothing says so."
            )
        if self.low.value >= self.high.value:
            raise ValueError(
                f"{self.applies_to}: plausible range [{self.low.value:g}, "
                f"{self.high.value:g}] is empty or inverted. With no range there is no safe "
                "side, and 'conservative' is a word rather than a check."
            )
        require_reportable(self.quantity)
        if not self.low.value <= self.quantity.value <= self.high.value:
            raise ValueError(
                f"{self.applies_to}: default {self.quantity.value:g} is outside its own "
                f"declared range [{self.low.value:g}, {self.high.value:g}]."
            )
        if self._is_on_the_unsafe_side():
            raise ValueError(
                f"{self.applies_to}: direction is {self.direction.name} but the default "
                f"{self.quantity.value:g} sits on the unsafe side of the range "
                f"[{self.low.value:g}, {self.high.value:g}]. This is the inversion rule 5 "
                "exists to catch: the declaration says be cautious, the number says the "
                "opposite, and the code runs either way."
            )

    def _is_on_the_unsafe_side(self) -> bool:
        """Wrong side of the midpoint.

        The midpoint is not a tuned threshold — it is the weakest possible statement of "on the
        safe side", chosen so the check catches the inversion without pretending to make the
        domain call about *how far*. See :meth:`position_in_range`.
        """
        midpoint = (self.low.value + self.high.value) / 2.0
        if self.direction is Conservatism.ASSUME_HIGH:
            return self.quantity.value < midpoint
        return self.quantity.value > midpoint

    @property
    def position_in_range(self) -> float:
        """Where the default sits, 0.0 at ``low`` and 1.0 at ``high``.

        Reported rather than constrained. A default at 0.55 of an ``ASSUME_HIGH`` range passes
        the inversion check and is probably still too timid to trigger any plant action, and
        that judgement belongs to someone who knows the plant.
        """
        return (self.quantity.value - self.low.value) / (self.high.value - self.low.value)

    def explain(self) -> str:
        unit = f" {self.quantity.unit}" if self.quantity.unit else ""
        return (
            f"{self.applies_to}: on abstention, emit {self.quantity.value:g}{unit} "
            f"({self.direction.value}, {self.position_in_range:.0%} of the way from "
            f"{self.low.value:g} to {self.high.value:g}). {self.quantity.cite()}"
        )


@dataclass(frozen=True, slots=True)
class Prediction:
    """A head answered. The ordinary case, here so the refusing case has something to sit beside."""

    head: str
    quantity: Quantity


@dataclass(frozen=True, slots=True)
class Abstention:
    """A head refused, and said why, and said what to do instead.

    Three fields, and the absence of a fourth is the point: there is nowhere to put the previous
    setpoint, so there is no way to hold it.

    :param reason: mandatory, specific, and not one of the usual non-reasons. Rule 5 names
        "unknown" explicitly because it is the one that gets typed.
    """

    default: ConservativeDefault
    reason: str
    trigger: AbstentionTrigger

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "an abstention must carry a reason. A refusal with no reason is indistinguishable "
                "from a crash, and an operator cannot act on either."
            )
        if self.reason.strip().lower() in _NON_REASONS:
            raise ValueError(
                f'"{self.reason}" is not a reason, it is the absence of one. Rule 5 names '
                '"unknown" specifically. Say what the system saw: which gate fired, on what '
                "feature, against which reference."
            )

    def emit(self) -> Quantity:
        """The number that goes to the controller. The conservative default, with its provenance."""
        return self.default.quantity

    def explain(self) -> str:
        """One line for the operator: what fired, what was seen, and what is being done instead."""
        return (
            f"abstained ({self.trigger.value}): {self.reason}. "
            f"Emitting the conservative default instead - {self.default.explain()}"
        )


Decision = Prediction | Abstention
"""A head either answered or refused. There is no third state, and neither state is silent."""


def value_to_act_on(decision: Decision) -> Quantity:
    """The one number a control loop reads, whichever way the decision went.

    Takes no previous value, on purpose. There is no parameter through which the last-known-good
    setpoint could be supplied, so "hold the last setpoint" is not an available behaviour rather
    than a discouraged one.
    """
    if isinstance(decision, Abstention):
        return decision.emit()
    return decision.quantity


@dataclass(frozen=True, slots=True)
class AbstentionAudit:
    """Abstention rate, split by whether the ore was changing. Never the aggregate alone.

    Blind spot 1 is not visible in a pooled rate, and a pooled rate is what gets quoted. So this
    type does not offer a headline number to quote: :meth:`summary` prints all three, always.
    """

    n_decisions: int
    n_abstentions: int
    n_ore_change: int
    n_abstentions_during_ore_change: int

    @property
    def n_stable(self) -> int:
        return self.n_decisions - self.n_ore_change

    @property
    def n_abstentions_when_stable(self) -> int:
        return self.n_abstentions - self.n_abstentions_during_ore_change

    @property
    def rate_overall(self) -> float:
        return self.n_abstentions / self.n_decisions

    @property
    def rate_during_ore_change(self) -> float:
        return self.n_abstentions_during_ore_change / self.n_ore_change

    @property
    def rate_when_stable(self) -> float:
        """Abstention rate away from transitions. ``0.0`` when every frame was a transition."""
        if self.n_stable == 0:
            return 0.0
        return self.n_abstentions_when_stable / self.n_stable

    @property
    def noise_during_ore_change(self) -> float | None:
        """``sqrt(p(1-p)/n)`` on the conditional rate, or ``None`` where that formula lies.

        Same arithmetic this package already quotes for conformal coverage SD and for
        :attr:`~reefprint.trust.baseline.ScoredMetric.noise_at_honest_n` — reused, not invented.
        Honest *n* here is the number of **ore-change events**, which is usually small, which is
        exactly why the conditional rate has to be reported with it attached.

        ``None`` at ``p = 0`` and ``p = 1``, because there the Wald standard error is exactly
        zero and that is not a statement about precision. Two abstentions out of two transitions
        would print as a flat ``0.0%`` interval — a claim of certainty produced by the *least*
        informative observation available, and small runs land on those extremes constantly.
        :attr:`bound_during_ore_change` covers those ends instead.
        """
        p = self.rate_during_ore_change
        if p in (0.0, 1.0):
            return None
        return sqrt(p * (1.0 - p) / self.n_ore_change)

    @property
    def bound_during_ore_change(self) -> float | None:
        """The rule of three, for the ends where the standard error degenerates.

        With zero events in *n* trials the 95% upper bound on the rate is ``3/n`` (Hanley &
        Lippman-Hand 1983) — a published result, not a threshold chosen here. Mirrored at the
        other end: *n* out of *n* puts the 95% lower bound at ``1 - 3/n``.

        ``None`` when ``3/n >= 1``, which at n = 2 it is. That is not a gap in the reporting, it
        *is* the reporting: two transitions bound nothing, and the line has to say so rather than
        print a number that suggests otherwise.
        """
        if self.rate_during_ore_change not in (0.0, 1.0):
            return None
        three_over_n = 3.0 / self.n_ore_change
        if three_over_n >= 1.0:
            return None
        return three_over_n if self.rate_during_ore_change == 0.0 else 1.0 - three_over_n

    @property
    def concentrates_at_transitions(self) -> bool:
        """Whether refusals cluster where they are most dangerous. Blind spot 1, as a boolean.

        A plain comparison of the two observed rates. Whether *n* can resolve the difference is
        a separate question, answered by :attr:`noise_during_ore_change` and printed alongside —
        the same division of labour as :class:`~reefprint.trust.baseline.ScoredMetric`, where the
        direction and the resolvability are two statements rather than one.
        """
        return self.rate_during_ore_change > self.rate_when_stable

    def summary(self) -> str:
        line = (
            f"abstention rate {self.rate_overall:.1%} overall · "
            f"{self.rate_during_ore_change:.1%} during ore change "
            f"(n = {self.n_ore_change}, {self._conditional_precision()}) · "
            f"{self.rate_when_stable:.1%} when stable (n = {self.n_stable})"
        )
        if self.concentrates_at_transitions:
            return (
                f"{line} — blind spot 1: refusals concentrate at the transitions, which is "
                "when holding the last setpoint is the worst available action"
            )
        return f"{line} — refusals do not concentrate at the transitions"

    def _conditional_precision(self) -> str:
        """What the conditional rate is actually worth, in words rather than a false interval."""
        if (noise := self.noise_during_ore_change) is not None:
            return f"±{noise:.1%}"
        if (bound := self.bound_during_ore_change) is None:
            return "which resolves nothing"
        if self.rate_during_ore_change == 0.0:
            return f"95% upper bound {bound:.0%} by the rule of three"
        return f"95% lower bound {bound:.0%} by the rule of three"


def audit_abstentions(
    decisions: Sequence[Decision], *, ore_change: Sequence[bool]
) -> AbstentionAudit:
    """Score a run of decisions against which frames were ore transitions.

    :param ore_change: one flag per decision. Where this comes from is a separate problem — a
        labelled sequence, a feed-grade step change, an operator's log — and it is a problem
        worth having, because without it the abstention rate is unreadable.

    :raises ValueError: on an empty run, a length mismatch, or **no ore-change events at all**.
        The last is the important one: with nothing to condition on, the only number available is
        the aggregate, and quoting the aggregate is precisely the error blind spot 1 describes.
        A gate that has never been tested through a transition has not been tested.
    """
    if len(decisions) == 0:
        raise ValueError(
            "cannot audit an empty run of decisions. An abstention rate over nothing is 0/0, "
            "and every way of rendering that is more flattering than the truth."
        )
    if len(decisions) != len(ore_change):
        raise ValueError(
            f"length mismatch: {len(decisions)} decisions against {len(ore_change)} ore-change "
            "flags. One flag per decision, or the conditional is computed against the wrong "
            "frames and still returns a number."
        )
    n_ore_change = sum(ore_change)
    if n_ore_change == 0:
        raise ValueError(
            f"no ore-change events in {len(decisions)} decisions, so the abstention rate cannot "
            "be conditioned on the only thing that matters. Refusing rather than returning the "
            "aggregate alone: blind spot 1 says novel texture trips the OOD gate and novel "
            "texture is an ore transition, so a run with no transitions cannot show whether the "
            "gate fires when it is least safe. Audit a run that contains one."
        )
    abstained = [isinstance(decision, Abstention) for decision in decisions]
    return AbstentionAudit(
        n_decisions=len(decisions),
        n_abstentions=sum(abstained),
        n_ore_change=n_ore_change,
        n_abstentions_during_ore_change=sum(
            1
            for was_abstention, changing in zip(abstained, ore_change, strict=True)
            if was_abstention and changing
        ),
    )
