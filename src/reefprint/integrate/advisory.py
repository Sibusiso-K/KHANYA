"""Dependency-free record boundary for advisory outputs."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AdvisoryRecord"]


@dataclass(frozen=True, slots=True)
class AdvisoryRecord:
    """One advisory observation with the endogeneity flag present from record zero."""

    values: dict[str, float]
    advisory_influenced: bool
    source: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("an advisory record must name its source")
        if not isinstance(self.advisory_influenced, bool):
            raise TypeError("advisory_influenced must be an explicit bool")
        if not all(isinstance(name, str) and name.strip() for name in self.values):
            raise ValueError("advisory value names must be non-empty strings")

    def as_dict(self) -> dict[str, object]:
        """Serialise a stable record shape for logs and downstream adapters."""
        return {
            "values": dict(self.values),
            "advisory_influenced": self.advisory_influenced,
            "source": self.source,
        }
