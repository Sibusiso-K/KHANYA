"""Operational feedback layer.

This is the part of the brief most teams will skip: turning phase identification
into a plant decision. The thresholds below are PLACEHOLDERS. Before the event,
each one must be replaced with a value backed by a citation or by a Mintek
contact, and the source recorded in the report. Judges from this sector will ask
where the numbers came from, and "we picked them" is a losing answer.
"""
from dataclasses import dataclass

# Placeholder thresholds - replace with sourced values. See module docstring.
GANGUE_PHASES = {"quartz"}
HIGH_GANGUE = 0.40          # gangue fraction above which the feed is diluted
LOW_LIBERATION = 0.65       # liberation below which regrinding is indicated
GOETHITE_PENALTY = 0.15     # goethite fraction that harms downstream handling


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
