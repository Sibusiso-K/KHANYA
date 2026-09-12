"""Dependency-free record boundary for advisory outputs.

Deliberately has no ``asyncua`` import. A record is a plain value with rule 1's provenance-shaped
discipline applied to a *decision* instead of a number: it must say when it was made, how long it
is good for, and whether it already changed the plant it describes (blind spot 10). The transport
that carries it — :mod:`reefprint.integrate.opcua_server` — is a separate, optional dependency;
the record itself must be constructible and testable without one.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from numbers import Real
from types import MappingProxyType

__all__ = ["AdvisoryRecord"]


@dataclass(frozen=True, slots=True)
class AdvisoryRecord:
    """One advisory observation with the endogeneity flag present from record zero.

    :param values: named quantities, one record can carry several heads (e.g. several
        structural-proxy risks computed from the same input). All must be finite.
    :param advisory_influenced: see the module docstring on blind spot 10. Mandatory, an
        explicit ``bool`` — ``0``/``1`` are refused so a numeric fixture cannot slip past a
        boolean-shaped check silently.
    :param source: mandatory and non-empty — what produced this record.
    :param unit: free text, one unit for the whole record. Consistent with
        :mod:`reefprint.quantity`'s convention: "" is the honest answer for a dimensionless
        fraction, never omit the field to mean that.
    :param emitted_at: unix epoch seconds. Defaults to "now" — this is a system timestamp, not a
        domain measurement, so a default factory does not violate rule 1.
    :param valid_for_seconds: the acknowledgement-and-expiry contract. A consumer must not act on
        a record once :meth:`is_expired` is true. Defaults to "never expires" so existing
        callers that do not yet reason about staleness are unaffected; a live deployment should
        always pass a finite window.
    """

    values: dict[str, float]
    advisory_influenced: bool
    source: str
    unit: str = ""
    emitted_at: float = field(default_factory=time.time)
    valid_for_seconds: float = math.inf

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("an advisory record must name its source")
        if not isinstance(self.advisory_influenced, bool):
            raise TypeError("advisory_influenced must be an explicit bool")
        if not all(isinstance(name, str) and name.strip() for name in self.values):
            raise ValueError("advisory value names must be non-empty strings")
        if not all(
            isinstance(v, Real) and not isinstance(v, bool) and math.isfinite(v)
            for v in self.values.values()
        ):
            raise ValueError(
                "advisory values must be finite numbers — a NaN or inf here would reach a "
                "control loop silently, which is exactly what the OPC UA quality state exists "
                "to prevent upstream of this type"
            )
        if not math.isfinite(self.emitted_at):
            raise ValueError("emitted_at must be a finite timestamp")
        if self.valid_for_seconds <= 0 or math.isnan(self.valid_for_seconds):
            raise ValueError(
                "valid_for_seconds must be positive — a non-positive window is expired the "
                "instant it is emitted, which is indistinguishable from never having a window "
                "at all and should be spelled as a very small positive number instead"
            )
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def is_expired(self, *, now: float | None = None) -> bool:
        """Whether a consumer must refuse to act on this record.

        :param now: unix epoch seconds. Defaults to the wall clock; pass a fixed value in tests
            so expiry is deterministic rather than racing the test runner.
        """
        current = time.time() if now is None else now
        return (current - self.emitted_at) > self.valid_for_seconds

    def as_dict(self) -> dict[str, object]:
        """Serialise a stable record shape for logs and downstream adapters."""
        return {
            "values": dict(self.values),
            "advisory_influenced": self.advisory_influenced,
            "source": self.source,
            "unit": self.unit,
            "emitted_at": self.emitted_at,
            "valid_for_seconds": self.valid_for_seconds,
        }
