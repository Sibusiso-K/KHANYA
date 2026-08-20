"""Rule 1, made structural: never invent a number; flag every assumption as an assumption.

The hardest of the standing rules, because there is nothing to detect. An invented number and a
measured one are the same 64 bits. ``0.35`` is ``0.35`` whether it came from a calibration run,
a textbook, a phantom, a plausible guess, or a specification for hardware that was never built.
No validator can tell them apart, because there is no malformed state — the number is fine. What
is missing is everything *around* the number, and by the time it reaches a slide, the person
reading it has no way to ask.

So the guard is not a check on the value. It is a property carried **with** the value, and it is
**contagious**: the moment an assumption enters a calculation, everything downstream of it is an
assumption too, whether or not anyone remembers. That is the part prose reliably fails at, since
the contamination surfaces three functions away from where the assumption was written down, in a
variable named something reasonable like ``grain_size_um``.

Five provenances, ordered by how far they sit from a measurement of real ore:

============== ==========================================================================
MEASURED       came out of data in this repository. The only kind of number that is a result.
CITED          published, with a citation. Craig & Vaughan, the IMA/COM QDF.
STIPULATED     true by construction — a phantom's parameters. Exactly true, of the phantom.
ASSUMED        a guess, stated as one. Permitted by rule 1, *if* it says so.
DESIGN_TARGET  a specification for the rig that was never built. Permitted nowhere.
============== ==========================================================================

Arithmetic keeps the **weakest** provenance of its inputs and accumulates their sources, so a
derived quantity can always say what fed it. :func:`require_reportable` is the boundary: call it
before any number is printed, plotted or put in a document.

``DESIGN_TARGET`` is the one provenance that cannot be reported at all, and that is not this
module's judgement — it is `ADR-0002
<../../docs/04-decisions/0002-software-only-no-instrument-is-built.md>`_ and CLAUDE.md, which say
of the 0.2-1.6 µm/pixel figure: *nothing may be derived from it*. The reason is visible in
:func:`~tests.test_quantity.test_the_design_target_spans_a_factor_of_eight_so_it_is_not_a_number`
— the two ends of that range differ by a factor of **8**, so a grain size derived from it is not
a measurement with wide error bars. It is a figure that could be 9 µm or 75 µm, printed to three
significant figures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

__all__ = [
    "Provenance",
    "Quantity",
    "assumed",
    "cited",
    "design_target",
    "measured",
    "require_reportable",
    "stipulated",
]


class Provenance(StrEnum):
    """Where a number came from. The thing that distinguishes 0.35 from 0.35.

    The value of each member is the phrase that appears in :meth:`Quantity.cite`, so the label
    a reader sees is the same string the code branches on. Two places to disagree is one too
    many.
    """

    MEASURED = "measured from data in this repository"
    CITED = "a published value, with a citation"
    STIPULATED = "true by construction (a phantom or synthetic parameter)"
    ASSUMED = "an assumption, stated as one"
    DESIGN_TARGET = "a design target for hardware that was never built"

    @property
    def distance_from_measurement(self) -> int:
        """Rank, 0 (measured) to 4 (design target). Higher is weaker."""
        return _DISTANCE[self]

    def is_stronger_than(self, other: Provenance) -> bool:
        return self.distance_from_measurement < other.distance_from_measurement


_DISTANCE: dict[Provenance, int] = {
    Provenance.MEASURED: 0,
    Provenance.CITED: 1,
    Provenance.STIPULATED: 2,
    Provenance.ASSUMED: 3,
    Provenance.DESIGN_TARGET: 4,
}


@dataclass(frozen=True, slots=True)
class Quantity:
    """A number that cannot be separated from where it came from.

    :param value: must be finite. A NaN is a number that was never measured, and letting one
        through is rule 1's failure with extra steps.
    :param unit: free text, but consistent text. ``+`` refuses mismatched units; ``*`` cancels
        a matching denominator so ``px`` times ``um/px`` is ``um`` rather than nonsense.
    :param source: mandatory and non-empty. For ``MEASURED``, what produced it; for ``CITED``,
        the citation; for ``ASSUMED``, the assumption in words. This is rule 1's second clause
        — *flag every assumption as an assumption* — and it is the field that makes the flag
        unavoidable rather than well-intentioned.
    :param derived_from: sources inherited through arithmetic. Set by the operators; you do not
        pass this.
    """

    value: float
    unit: str
    provenance: Provenance
    source: str
    derived_from: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError(
                f"a Quantity must state its source. {self.value} {self.unit} with no source is "
                "exactly the unlabelled number rule 1 forbids — say what measured it, cite it, "
                "or state the assumption in words."
            )
        if not isfinite(self.value):
            raise ValueError(
                f"a Quantity must be finite, got {self.value} ({self.source}). A NaN or an "
                "infinity is a number that was never measured, and it propagates silently."
            )

    # -- provenance ----------------------------------------------------------------------

    @property
    def all_sources(self) -> tuple[str, ...]:
        """Every source that fed this number, nearest first, each named once."""
        return _dedupe((self.source, *self.derived_from))

    @property
    def is_reportable(self) -> bool:
        return self.provenance is not Provenance.DESIGN_TARGET

    def cite(self) -> str:
        """The number, its provenance and its full source trail, in one line.

        Rule 1 says *in the code and in the docs*. This is the docs half: whatever goes into a
        figure caption or a slide comes from here, so the label cannot drift from the value.
        """
        unit = f" {self.unit}" if self.unit else ""
        sources = "; ".join(self.all_sources)
        return f"{self.value:g}{unit} — {self.provenance.value}. Source: {sources}"

    # -- arithmetic, which is where the contamination happens ----------------------------

    def __add__(self, other: object) -> Quantity:
        return self._combine(other, "+")

    def __sub__(self, other: object) -> Quantity:
        return self._combine(other, "-")

    def __mul__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self._derive(_multiply_units(self.unit, other.unit), self.value * other.value, other)

    def __truediv__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self._derive(_divide_units(self.unit, other.unit), self.value / other.value, other)

    def __float__(self) -> float:
        """The obvious way around any wrapper, closed for the one provenance that forbids it.

        An assumption converts freely: rule 1 permits assumptions, it requires them to be
        labelled, and by the time you hold a ``Quantity`` it has been. A design target does not
        convert at all.
        """
        require_reportable(self)
        return self.value

    def _combine(self, other: object, operator: str) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        if self.unit != other.unit:
            raise ValueError(
                f"cannot {operator} quantities with different units: "
                f"{self.unit!r} ({self.source}) and {other.unit!r} ({other.source})."
            )
        value = self.value + other.value if operator == "+" else self.value - other.value
        return self._derive(self.unit, value, other)

    def _derive(self, unit: str, value: float, other: Quantity) -> Quantity:
        """Build the result, keeping the weaker provenance and both source trails."""
        sources = _dedupe(self.all_sources + other.all_sources)
        weaker = (
            self.provenance
            if self.provenance.distance_from_measurement
            >= other.provenance.distance_from_measurement
            else other.provenance
        )
        return Quantity(
            value=value,
            unit=unit,
            provenance=weaker,
            source=sources[0],
            derived_from=sources[1:],
        )


def measured(value: float, unit: str, source: str) -> Quantity:
    """A number that came out of data in this repository. The only kind that is a result."""
    return Quantity(value=value, unit=unit, provenance=Provenance.MEASURED, source=source)


def cited(value: float, unit: str, source: str) -> Quantity:
    """A published value. ``source`` is the citation, specific enough to check."""
    return Quantity(value=value, unit=unit, provenance=Provenance.CITED, source=source)


def stipulated(value: float, unit: str, source: str) -> Quantity:
    """A phantom's parameter — exactly true, of the phantom, and of nothing else.

    Kept distinct from ``MEASURED`` because experiment 001's ground truth is a construction.
    It proves the maths, not the mineralogy, and the type should not let that blur.
    """
    return Quantity(value=value, unit=unit, provenance=Provenance.STIPULATED, source=source)


def assumed(value: float, unit: str, source: str) -> Quantity:
    """A guess. Permitted by rule 1, provided ``source`` states the assumption in words."""
    return Quantity(value=value, unit=unit, provenance=Provenance.ASSUMED, source=source)


def design_target(value: float, unit: str, source: str) -> Quantity:
    """A specification for the rig that was never built. Nothing may be derived from it.

    Constructing one is allowed so the figure can be quoted *as a design target* — which is how
    ADR-0002 says to present it. Reporting anything computed from it is not.
    """
    return Quantity(value=value, unit=unit, provenance=Provenance.DESIGN_TARGET, source=source)


def require_reportable(quantity: Quantity) -> None:
    """Refuse to let a design-target-derived number reach a slide, a plot or a document.

    Call this at the boundary — anywhere a number stops being an intermediate and starts being
    a claim. Assumptions pass, because rule 1 permits a flagged assumption and the flag travels
    with the value. Design targets do not, because ADR-0002 says *nothing may be derived from
    it*, and by the time the number has a unit and three significant figures nobody can tell.

    :raises ValueError: naming every source that fed the quantity, so the poisoned input is
        identifiable from the traceback rather than three functions away from it.
    """
    if quantity.provenance is Provenance.DESIGN_TARGET:
        raise ValueError(
            f"refusing to report {quantity.value:g} {quantity.unit}: it derives from a design "
            "target for hardware that was never built. ADR-0002 and CLAUDE.md both say nothing "
            "may be derived from it — the 0.2 and 1.6 ends of that range differ by a factor of "
            "8, so this is not a measurement with wide error bars, it is not a measurement. "
            f"Sources: {'; '.join(quantity.all_sources)}."
        )


def _dedupe(items: tuple[str, ...]) -> tuple[str, ...]:
    """Order-preserving deduplication. One source, named once, however many times it fed in."""
    return tuple(dict.fromkeys(items))


def _multiply_units(left: str, right: str) -> str:
    """``px`` times ``um/px`` is ``um``. One cancellation rule, because a scale factor is where
    invented numbers get in, and ``px*um/px`` in a caption is how they stay in."""
    if not left:
        return right
    if not right:
        return left
    for ratio, other in ((left, right), (right, left)):
        top, slash, bottom = ratio.partition("/")
        if slash and bottom == other:
            return top
    return f"{left}*{right}"


def _divide_units(left: str, right: str) -> str:
    if left == right:
        return ""
    if not right:
        return left
    return f"{left}/{right}"
