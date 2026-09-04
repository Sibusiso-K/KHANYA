"""Operational feedback layer.

Reasons over metallurgical ROLES (payload / reject / oxide / gangue /
deleterious), not mineral names, so the same decision logic serves LumenStone S2
today and the REEFPRINT phase set if Mintek releases data - see src/modal.py,
where the mineral-to-role mapping lives. Swapping ore bodies should change a
mapping, not this file.

Inputs are measured, not asserted: phase fractions come from segmented area,
liberation from particle composition (src/modal.py). The earlier version of this
module took classifier confidences as if they were area fractions and took
liberation from a UI slider - neither was a measurement, and both are gone.

Threshold sourcing status, checked 2026-08-14. Stated plainly because claiming
sourced numbers we do not have is a worse failure than admitting placeholders:

- LOW_LIBERATION: SOURCED. Composite-particle recovery in conventional flotation
  drops considerably once surface exposure falls below ~50%, further below ~25%
  (911 Metallurgist, "Grinding for Liberation and Flotation"). Olympic Dam runs
  a two-stage grind (P80 75um, regrind to P80 30um; AusIMM 2024 Mill Operators'
  Conference) specifically to hit a liberation target - corroborates this as a
  real operating lever, not an invented number.
- PAYLOAD_FLOOR: NOT sourced to a numeric value. It answers "is there enough
  payload in this field to say anything at all", and needs a real per-deposit
  assay reference before the event.
- REJECT_CEILING: NOT sourced to a numeric value. Pyrrhotite rejection is
  established practice in magmatic Ni-Cu processing (grade dilution, smelter
  sulphur load), but the fraction at which a plant acts is deposit- and
  smelter-contract-specific.
- DELETERIOUS_CEILING: NOT sourced to a numeric value. Talc is naturally
  floatable and drives depressant demand in PGM flotation - that is the
  REEFPRINT abstract's own reason for including the phase - but no source gives
  a numeric fraction threshold.
"""
from dataclasses import dataclass

LOW_LIBERATION = 0.50        # SOURCED - see module docstring
PAYLOAD_FLOOR = 0.003        # UNSOURCED placeholder
REJECT_CEILING = 0.60        # UNSOURCED placeholder
DELETERIOUS_CEILING = 0.05   # UNSOURCED placeholder

# Uncertainty band around the liberation threshold.
#
# CORRECTED 2026-08-18. This was originally the mean absolute error of the
# liberation estimate (8.9%) used as a symmetric half-width - a point estimate
# presented with the shape of a guarantee. Checked against its own data: a
# fixed +/-8.9% band actually covers only 67% of S2 sections and 45% of S1
# sections, not the ~90% the word "band" implies. See src/conformal.py and
# report section 5.0.8 for the full derivation.
#
# Replaced with a split-conformal half-width: the empirical 85th-percentile
# absolute residual under leave-one-out calibration on the 12 S2 test sections
# (reports/conformal_decision_gap_patches_refined.json). 85% rather than 90%
# because 1 - 1/(n+1) = 92.3% is the highest level n=12 can support at all, and
# we report the achievable level rather than claim one the data cannot back.
# This is therefore a genuine distribution-free coverage guarantee under
# exchangeability, not a dressed-up point estimate.
#
# The width nearly quadrupled (0.089 -> 0.335) versus the original constant.
# That is the correction, not a regression: the old band was overconfident,
# and a wider honest band that hedges more often is the right trade for a
# system whose entire differentiator is knowing when not to guess.
#
# Re-derive whenever the estimator, dataset, or calibration set size changes -
# it is a property of the measurement chain, not a tuned preference. Run
# `python -m src.conformal --run <decision_gap file>` to recompute.
LIBERATION_MARGIN = 0.335

# Below this, the field is mostly mounting resin and any area fraction computed
# from it is derived from too few ore pixels to act on.
MIN_ORE_AREA = 0.05


@dataclass
class Recommendation:
    action: str
    reason: str
    confidence: str


def advise(result, mean_confidence: float,
           liberation_margin: float = LIBERATION_MARGIN) -> Recommendation:
    """result: a modal.ModalResult. Returns one operational recommendation.

    liberation_margin: half-width of the uncertainty band around the liberation
    threshold. Pass 0.0 when the input is a ground-truth mask - an annotation
    carries no estimator error, so banding it would compare a hedged reference
    against a hedged prediction and hide exactly the disagreement we are trying
    to measure.

    Checked in payload-first order. A low or unmeasurable payload signal is
    reported explicitly rather than falling through to "continue", because
    silently continuing on a field where the payload was never detected is the
    exact failure mode this module exists to catch: a model can score well on
    aggregate accuracy while missing the phase that carries all the value.
    """
    confidence = "high" if mean_confidence >= 0.85 else "low - verify manually"
    payload = result.role_fractions.get("payload", 0.0)

    if result.ore_area_fraction < MIN_ORE_AREA:
        return Recommendation(
            "No recommendation - insufficient ore in field",
            f"Only {result.ore_area_fraction:.1%} of this field is ore; the rest "
            "is mounting resin. Area fractions from this section are computed "
            "over too few pixels to act on. Re-image or re-section.",
            confidence,
        )

    if not result.has_payload:
        return Recommendation(
            "Flag for manual review - no payload detected",
            "No payload phase was segmented anywhere in this field. Treat this "
            "as an unmeasured result, not as a zero-grade result: absence of "
            "detection and absence of mineral are different claims, and this is "
            "the sub-1% class that carries the economic value.",
            confidence,
        )

    if payload < PAYLOAD_FLOOR:
        return Recommendation(
            "Flag for manual review - low payload signal",
            f"Payload phases occupy {payload:.2%} of ore area, below the "
            f"{PAYLOAD_FLOOR:.2%} floor. Do not report confidence on aggregate "
            "accuracy alone - a model can score well overall while effectively "
            "missing this class.",
            confidence,
        )

    if result.liberation is None:
        return Recommendation(
            "Flag for manual review - liberation not measurable",
            "Payload is present but no particle cleared the minimum size for a "
            "liberation measurement. Reported as unmeasured rather than as a "
            "number we cannot defend.",
            confidence,
        )

    if abs(result.liberation - LOW_LIBERATION) < liberation_margin:
        return Recommendation(
            "Marginal - verify before acting",
            f"Liberation is {result.liberation:.0%}, within the "
            f"+/-{liberation_margin:.1%} conformal uncertainty band around the "
            f"{LOW_LIBERATION:.0%} floor (85% empirical coverage, held-out "
            "sections; see src/conformal.py). The true value could plausibly "
            "sit on either side of the threshold, so the honest answer is that "
            "this field does not decide. Candidate actions are 'grind finer' if "
            "liberation is genuinely below the floor, or 'continue at setpoint' "
            "if above. Confirm with an additional field or an assay before "
            "changing the circuit.",
            confidence,
        )

    if result.liberation < LOW_LIBERATION:
        return Recommendation(
            "Grind finer",
            f"Liberation is {result.liberation:.0%}, below the "
            f"{LOW_LIBERATION:.0%} floor, across {result.n_particles} particles. "
            "Payload locked in composite particles will report to tailings and "
            "depress recovery. Note this figure is an upper bound - apparent "
            "liberation from 2D sections is biased high against true volumetric "
            "liberation, so the real case for grinding is at least this strong.",
            confidence,
        )

    reject = result.role_fractions.get("reject", 0.0)
    if reject > REJECT_CEILING:
        return Recommendation(
            "Adjust reagent dosage - depress reject phase",
            f"Reject phases occupy {reject:.0%} of ore area against "
            f"{payload:.0%} payload. Payload is adequately liberated, so the "
            "constraint is concentrate grade rather than grind: raise depressant "
            "dosage to reject the barren sulphide rather than grinding further, "
            "which would spend energy without improving recovery.",
            confidence,
        )

    deleterious = result.role_fractions.get("deleterious", 0.0)
    if deleterious > DELETERIOUS_CEILING:
        return Recommendation(
            "Adjust reagent dosage - raise depressant",
            f"Deleterious phases at {deleterious:.0%} of ore area raise "
            "depressant demand; talc and serpentine are naturally floatable and "
            "compete with sulphides for flotation response.",
            confidence,
        )

    return Recommendation(
        "Continue at current setpoint",
        f"Payload at {payload:.0%} of ore area, liberation {result.liberation:.0%} "
        f"across {result.n_particles} particles, no phase over its threshold.",
        confidence,
    )


# --- Presentation state -----------------------------------------------------
#
# The dashboard renders three verdict colours, and this decides which. It lives
# here rather than in the dashboard because it is a statement about the
# decision layer's own severity, not about styling, and because the invariant
# below is worth a test rather than an eyeball.

#: Recommendations on which the advisor is declining to decide. Everything here
#: renders amber; nothing else may. A confident continue is green and a
#: confident grind is red - both are decisions, and neither may borrow the
#: colour that means "do not act on this yet". Keeping the rule in one place is
#: what makes "amber on stage always means the same thing" checkable.
ABSTAINING_PREFIXES = ("Marginal", "Flag", "No recommendation")


def verdict_state(action: str) -> tuple[str, str]:
    """(css class, state label) for a recommendation's action string.

    The css class is "" for a confident continue, "grind" for a confident
    intervention, and "hold" for every case where the system is abstaining.
    """
    if action.startswith("Marginal"):
        return "hold", "verdict state: marginal, verify before acting"
    if action.startswith(("Flag", "No recommendation")):
        return "hold", "verdict state: measurement declined"
    if action.startswith("Grind"):
        return "grind", "verdict state: confident intervention"
    return "", "verdict state: within specification"
