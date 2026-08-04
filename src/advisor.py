"""Operational feedback layer, re-scoped to the REEFPRINT phase set
(chromite, orthopyroxene, plagioclase, base-metal sulphide, talc/serpentine -
see src/config.py REEFPRINT_CLASSES). Typical Bushveld UG2 volume fractions
per the abstract: chromite ~50-75%, orthopyroxene ~15-30%, plagioclase ~3-9%,
base-metal sulphide (BMS) <1% but carries essentially all the PGM value.

This inverts the usual advisor logic: BMS is not a gangue phase to threshold
away, it is the payload despite being a rounding error by area. A model or
advisor that treats low BMS area as "nothing here" is exactly the failure mode
the abstract calls out (97% aggregate accuracy from predicting "chromite" and
missing the sulphides entirely).

Threshold sourcing status, checked 2026-08-04:
- LOW_LIBERATION: SOURCED. Composite-particle recovery in conventional flotation
  drops considerably once surface exposure falls below ~50%, further below ~25%
  (911 Metallurgist, "Grinding for Liberation and Flotation"). Olympic Dam runs
  a two-stage grind (P80 75um then regrind to P80 30um, AusIMM 2024 Mill
  Operators' Conference) specifically to hit a liberation target - corroborates
  this as a real operating lever, not an invented number.
- BMS_FLOOR: NOT sourced to a numeric value. <1 vol% BMS is stated in the
  abstract as typical for UG2; the 0.003 floor here is a placeholder for "is
  there enough signal to bother reporting a recommendation at all" and needs a
  real per-deposit assay reference before the event.
- TALC_PENALTY: NOT sourced to a numeric value. Talc's flotation behaviour
  (naturally floatable, drives depressant reagent demand in PGM flotation) is
  the abstract's own stated reason for including this phase, but no numeric
  fraction threshold has been sourced yet.
"""
from dataclasses import dataclass

GANGUE_PHASES = {"Orthopyroxene", "Plagioclase"}
LOW_LIBERATION = 0.50        # SOURCED - see module docstring
BMS_FLOOR = 0.003            # UNSOURCED placeholder - see module docstring
TALC_PENALTY = 0.05          # UNSOURCED placeholder - see module docstring


@dataclass
class Recommendation:
    action: str
    reason: str
    confidence: str


def gangue_fraction(phase_fractions: dict) -> float:
    return sum(v for k, v in phase_fractions.items() if k in GANGUE_PHASES)


def advise(phase_fractions: dict, liberation: float, mean_confidence: float):
    """phase_fractions: {phase_name: area fraction}, summing to ~1.0.

    Checked in payload-first order: a low BMS reading is reported explicitly
    rather than falling through silently, since that is the failure mode this
    module exists to catch.
    """
    total = sum(phase_fractions.values())
    if not 0.95 <= total <= 1.05:
        raise ValueError(f"phase fractions sum to {total:.3f}, expected ~1.0")

    confidence = "high" if mean_confidence >= 0.85 else "low - verify manually"
    bms = phase_fractions.get("Base_Metal_Sulphide", 0.0)

    if bms < BMS_FLOOR:
        return Recommendation(
            "Flag for manual review - low payload signal",
            f"Base-metal sulphide at {bms:.2%} is below the {BMS_FLOOR:.2%} "
            "floor. Do not report high confidence on aggregate accuracy alone: "
            "this is the sub-1% class that carries the PGM value, and a model "
            "can score well overall while missing it entirely.",
            confidence,
        )

    if liberation < LOW_LIBERATION:
        return Recommendation(
            "Grind finer",
            f"Liberation at {liberation:.0%} is below {LOW_LIBERATION:.0%}; "
            "locked BMS particles will report to tailings and depress recovery.",
            confidence,
        )

    if phase_fractions.get("Talc_Serpentine", 0.0) > TALC_PENALTY:
        return Recommendation(
            "Adjust reagent dosage",
            f"Talc/serpentine at {phase_fractions['Talc_Serpentine']:.0%} "
            "raises depressant demand; talc is naturally floatable and competes "
            "with sulphides for flotation response.",
            confidence,
        )

    return Recommendation(
        "Continue at current setpoint",
        "BMS signal, liberation and gangue phases are all within nominal range.",
        confidence,
    )
