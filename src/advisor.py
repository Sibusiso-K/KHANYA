"""Operational feedback layer.

This is the part of the brief most teams will skip: turning phase identification
into a plant decision. Threshold sourcing status, checked 2026-08-04:

- LOW_LIBERATION: SOURCED. Composite-particle recovery in conventional flotation
  drops considerably once surface exposure falls below ~50%, and drops further
  below ~25% (911 Metallurgist, "Grinding for Liberation and Flotation").
  Olympic Dam runs primary grind P80 75um with regrind to P80 30um (AusIMM 2024
  Mill Operators' Conference) - a real plant using a two-stage grind specifically
  to hit a liberation target, corroborating that this is a real operating lever,
  not a made-up number.
- HIGH_GANGUE: NOT a universal constant. Economically this is the cutoff grade
  concept (Wikipedia "Cutoff grade"; MNG 230 course notes) - the grade at which
  processing cost equals commodity value - and it is deposit- and price-specific,
  not a fixed fraction. The 0.40 below is a placeholder for demo purposes only;
  a real deployment would compute this from current commodity price and cost,
  not read it off a constant.
- GOETHITE_PENALTY: NOT sourced. Goethite's practical effect (needs agglomeration
  before blast furnace use, dehydrates during sintering) is well documented
  (IspatGuru, "The Sintering Process of Iron Ore Fines"), but no source found
  gives a numeric goethite-fraction threshold - it is plant- and process-specific.
  Also note: this threshold assumes an iron-ore mineral set (hematite/magnetite/
  goethite/quartz) left over from the original scaffold. The dataset actually in
  use (MUMDMC2025: biotite/hornblende/plagioclase/K-feldspar/quartz) is igneous
  silicates, not iron ore - goethite will not appear in that data. Re-derive
  thresholds for whichever mineral set the final submission actually uses.
"""
from dataclasses import dataclass

GANGUE_PHASES = {"quartz"}
HIGH_GANGUE = 0.40          # UNSOURCED placeholder - see module docstring
LOW_LIBERATION = 0.50       # SOURCED - see module docstring
GOETHITE_PENALTY = 0.15     # UNSOURCED placeholder - see module docstring


@dataclass
class Recommendation:
    action: str
    reason: str
    confidence: str


def gangue_fraction(phase_fractions: dict) -> float:
    return sum(v for k, v in phase_fractions.items() if k in GANGUE_PHASES)


def advise(phase_fractions: dict, liberation: float, mean_confidence: float):
    """phase_fractions: {phase_name: area fraction}, summing to ~1.0."""
    total = sum(phase_fractions.values())
    if not 0.95 <= total <= 1.05:
        raise ValueError(f"phase fractions sum to {total:.3f}, expected ~1.0")

    confidence = "high" if mean_confidence >= 0.85 else "low - verify manually"

    if gangue_fraction(phase_fractions) > HIGH_GANGUE:
        return Recommendation(
            "Divert feed",
            f"Gangue at {gangue_fraction(phase_fractions):.0%} exceeds the "
            f"{HIGH_GANGUE:.0%} dilution threshold; processing at grade wastes "
            "mill energy.",
            confidence,
        )

    if liberation < LOW_LIBERATION:
        return Recommendation(
            "Grind finer",
            f"Liberation at {liberation:.0%} is below {LOW_LIBERATION:.0%}; "
            "locked particles will report to tailings and depress recovery.",
            confidence,
        )

    if phase_fractions.get("goethite", 0.0) > GOETHITE_PENALTY:
        return Recommendation(
            "Adjust reagent dosage",
            f"Goethite at {phase_fractions['goethite']:.0%} raises moisture "
            "retention and handling load downstream.",
            confidence,
        )

    return Recommendation(
        "Continue at current setpoint",
        "Phase distribution and liberation are both within nominal range.",
        confidence,
    )
