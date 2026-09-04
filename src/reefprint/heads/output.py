"""Common, interval-bearing output contract for prediction heads."""

from __future__ import annotations

from dataclasses import dataclass

from reefprint.quantity import Quantity, require_reportable

__all__ = ["HeadEstimate"]


@dataclass(frozen=True, slots=True)
class HeadEstimate:
    """A reportable head value that cannot be constructed without its confidence interval."""

    head: str
    estimate: Quantity
    lower: Quantity
    upper: Quantity
    confidence: float

    def __post_init__(self) -> None:
        if not self.head.strip():
            raise ValueError("a head estimate must name its output")
        if not 0.0 < self.confidence < 1.0:
            raise ValueError("confidence must be strictly between zero and one")
        quantities = (self.estimate, self.lower, self.upper)
        if len({quantity.unit for quantity in quantities}) != 1:
            raise ValueError("estimate and interval bounds must use the same unit")
        if not self.lower.value <= self.estimate.value <= self.upper.value:
            raise ValueError("estimate must lie inside its interval")
        for quantity in quantities:
            require_reportable(quantity)

    def interval(self) -> tuple[float, float]:
        """Return numeric bounds only after provenance validation in construction."""
        return self.lower.value, self.upper.value
