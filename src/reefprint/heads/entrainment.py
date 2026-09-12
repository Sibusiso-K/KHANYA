"""Fine-chromite entrainment risk — the head that survived the v2 retarget (gauntlet F4).

**The mechanism, and why it is a structural proxy rather than a metallurgical measurement.**
Entrainment is the classical, non-selective route by which fine particles report to the froth
product regardless of hydrophobicity: they ride the water that carries between bubbles rather
than attaching to one. The standard framework (Trahar 1976; Johnson 1972; Savassi et al. 1998
formalise it as a size-dependent classification function) writes the entrained recovery of one
size class as

    ENT = EF(d) * Rw

with ``EF(d)`` the entrainment (classification) factor at particle size ``d`` — near 1 for
ultrafine particles, falling toward 0 as ``d`` grows — and ``Rw`` the fractional water recovery
to the froth. Extended here to one mineral's contribution to a feed:

    risk = chromite_mass_fraction * fine_fraction * entrainment_factor * water_recovery

``chromite_mass_fraction`` is how much of the feed is chromite at all; ``fine_fraction`` is how
much of *that* chromite sits below the size cutoff ``entrainment_factor`` was evaluated at. The
product is the expected mass fraction of the whole feed that is fine chromite riding into the
froth by entrainment — a **risk to concentrate grade and a smelter-penalty driver**, not a
recovery benefit, since UG2 flotation wants chromite rejected (CLAUDE.md's physics table).

**This module computes the formula. It does not choose the four numbers that go into it.**
Rule 6 forbids an LLM computing a mineralogical value, and picking ``entrainment_factor`` (which
literature classification curve, at which size cutoff) and ``water_recovery`` (which plant's
typical range) are exactly that kind of domain call — CLAUDE.md's own standing check on the
domain lead's role (blind spot 8) says a load-bearing mineralogical claim must not rest on one
person's judgement alone, and it must not rest on this module's judgement at all. Every
:class:`BoundedFraction` this function is given must already carry its own :class:`~reefprint.
quantity.Quantity` provenance — ``CITED`` with the paper, or ``ASSUMED`` and stated as such —
supplied by the caller, never invented here.

**The interval is a bound, not a statistical propagation.** The four inputs are a mix of
measured, cited and assumed structural quantities, not four independent random draws with known
distributions — a normal-approximation confidence interval would claim a precision this proxy
does not have (Rule 4). Instead the reported interval is the worst-case product of the four
inputs' own low ends against the best-case product of their high ends, which is a valid bound
because every factor lies in ``[0, 1]``: for nonnegative ``a_low <= a <= a_high`` and
``b_low <= b <= b_high``, ``a_low*b_low <= a*b_low <= a*b <= a*b_high <= a_high*b_high``, and the
same chaining extends to four factors. Pinned by
``test_the_worst_case_bound_brackets_the_point_estimate_for_any_valid_inputs``.
"""

from __future__ import annotations

from dataclasses import dataclass

from reefprint.heads.output import HeadEstimate
from reefprint.quantity import Quantity, require_reportable
from reefprint.trust.abstain import Conservatism, ConservativeDefault

__all__ = [
    "BoundedFraction",
    "entrainment_risk_conservative_default",
    "fine_chromite_entrainment_risk",
]

_HEAD_NAME = "fine_chromite_entrainment_risk"


@dataclass(frozen=True, slots=True)
class BoundedFraction:
    """A dimensionless fraction in ``[0, 1]`` together with a plausible range, all as
    :class:`~reefprint.quantity.Quantity`.

    Deliberately mirrors :class:`~reefprint.trust.abstain.ConservativeDefault`'s shape:
    multiplying several structural inputs together for a proxy needs the same "declare a low, a
    high, and check the point sits between them" discipline rule 5 already applies to a default.
    Kept local to this head rather than promoted to :mod:`reefprint.heads.output` until a second
    head needs the same contract — see the naturally-floating-gangue-load and oxidation-index
    heads on the backlog.
    """

    quantity: Quantity
    low: Quantity
    high: Quantity

    def __post_init__(self) -> None:
        units = {self.quantity.unit, self.low.unit, self.high.unit}
        if units != {""}:
            raise ValueError(
                f"a BoundedFraction must be dimensionless (unit ''), got {sorted(units)!r}. "
                "A fraction with a unit attached is a sign the wrong Quantity was passed in."
            )
        if self.low.value >= self.high.value:
            raise ValueError(
                f"plausible range [{self.low.value:g}, {self.high.value:g}] is empty or "
                "inverted — with no range there is no bound to compute."
            )
        for name, bound in (("quantity", self.quantity), ("low", self.low), ("high", self.high)):
            if not 0.0 <= bound.value <= 1.0:
                raise ValueError(f"{name} must be a fraction in [0, 1], got {bound.value:g}")
        if not self.low.value <= self.quantity.value <= self.high.value:
            raise ValueError(
                f"quantity {self.quantity.value:g} is outside its own declared range "
                f"[{self.low.value:g}, {self.high.value:g}]"
            )
        require_reportable(self.quantity)
        require_reportable(self.low)
        require_reportable(self.high)

    def __mul__(self, other: BoundedFraction) -> BoundedFraction:
        return BoundedFraction(
            quantity=self.quantity * other.quantity,
            low=self.low * other.low,
            high=self.high * other.high,
        )


def fine_chromite_entrainment_risk(
    *,
    chromite_mass_fraction: BoundedFraction,
    fine_fraction: BoundedFraction,
    entrainment_factor: BoundedFraction,
    water_recovery: BoundedFraction,
    confidence: float = 0.95,
) -> HeadEstimate:
    """The entrainment-risk structural proxy, as a reportable interval-bearing estimate.

    :param chromite_mass_fraction: how much of the feed is chromite at all.
    :param fine_fraction: how much of that chromite sits below the size cutoff
        ``entrainment_factor`` was evaluated at.
    :param entrainment_factor: the classification-function value at that cutoff (Trahar 1976 /
        Savassi et al. 1998 framework) — a literature or calibration-derived quantity, cited or
        assumed by the caller, never invented in this module.
    :param confidence: the nominal confidence the caller intends to attach to the *bound*
        below — reported for consistency with :class:`~reefprint.heads.output.HeadEstimate`'s
        contract, not because the bound is a statistical confidence interval in the usual sense
        (see the module docstring).

    :raises ValueError: from :class:`~reefprint.heads.output.HeadEstimate`'s own construction
        guard if any input carries a ``DESIGN_TARGET`` provenance, or if the resulting estimate
        somehow fails to lie inside its own bound (which the multiplication proof above rules
        out for valid inputs — a failure here would mean an input's own range was invalid in a
        way :class:`BoundedFraction` should already have refused).
    """
    combined = chromite_mass_fraction * fine_fraction * entrainment_factor * water_recovery
    return HeadEstimate(
        head=_HEAD_NAME,
        estimate=combined.quantity,
        lower=combined.low,
        upper=combined.high,
        confidence=confidence,
    )


def entrainment_risk_conservative_default(
    *, high: Quantity, low: Quantity, default: Quantity
) -> ConservativeDefault:
    """The abstention default for this head — ``ASSUME_HIGH``, per CLAUDE.md rule 5 and the
    worked example already named in :mod:`reefprint.trust.abstain`'s own module docstring:
    *"Entrainment risk and naturally-floating-gangue load are ASSUME_HIGH — over-dose the
    depressant, cut the feed, lose a little recovery."*

    Assuming high entrainment risk when the head cannot answer costs a little recovery; assuming
    low would under-dose the depressant exactly when the ore has changed and the risk is
    actually elevated — the inversion rule 5's guard exists to catch. This function does not
    choose ``low``, ``high`` or ``default`` itself; a caller (the domain lead, or a calibration
    run) must supply them, each already a :class:`~reefprint.quantity.Quantity` with its own
    provenance.
    """
    return ConservativeDefault(
        applies_to=_HEAD_NAME,
        quantity=default,
        direction=Conservatism.ASSUME_HIGH,
        low=low,
        high=high,
    )
