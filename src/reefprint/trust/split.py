"""Rule 2, made structural: split by locality, never by patch or image.

The constitution says a patch-level split *"will silently invalidate every metric"*. The word
doing the work is **silently**. A patch split does not raise, does not warn, and returns a
*better* number than the honest split — so the mistake is indistinguishable from success right
up until someone else fails to reproduce it. Prose is the wrong medium for a hazard whose whole
nature is that nothing prompts you to go and re-read the prose.

What leaks, concretely. Patches cut from one polished section share its illumination, its polish
quality, its resin, its embedding batch and its grain population. A model that has seen half of
a section's patches does not need to have learned any transferable mineralogy to score well on
the other half — it only needs to recognise the section. Locality is the coarsest unit at which
that shared nuisance structure plausibly stops, which is why it is the unit the rule names.

The exchangeability argument is the same one and it is worse. Conformal prediction guarantees
coverage only if calibration and test points are exchangeable. Patches from one section are not
exchangeable with patches from another locality: they are drawn from a tighter distribution.
Calibrate on a patch-level split and the conformal interval is a number with no guarantee behind
it, quoted to three digits.

So :func:`split_by_locality` is the sanctioned constructor, and :func:`require_locality_disjoint`
is the backstop for splits built by hand, which is the route around any constructor.

The other half of the rule is arithmetic. :attr:`LocalitySplit.n_groups` is the number of
localities, **not** the number of sections, because that is the honest *n* for rule 4. Six
sections drawn from three localities is n = 3. Quoting n = 6 narrows every confidence interval
on the slide by a factor of √2, and it is the kind of arithmetic a judge can redo in their head.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

__all__ = [
    "Grouped",
    "LocalitySplit",
    "require_locality_disjoint",
    "split_by_locality",
]


@runtime_checkable
class Grouped(Protocol):
    """Anything that knows which section and which locality it came from.

    Deliberately narrower than :class:`~reefprint.bridge.measure.SectionMeasurement`. The guard
    has to work on whatever unit is actually being split — sections, patches, grains — because
    the failure it prevents happens at the *patch* level, and a guard that only accepts sections
    is a guard that is absent exactly when it is needed.
    """

    section_id: str
    locality: str


@dataclass(frozen=True, slots=True)
class LocalitySplit:
    """A train/test split whose localities are disjoint by construction.

    Carries the counts it was built with so that a downstream metric can quote honest *n*
    without recomputing it — and without the temptation to quote the flattering one.
    """

    train: tuple[Grouped, ...]
    test: tuple[Grouped, ...]
    held_out: tuple[str, ...]
    n_dropped_unmeasured: int = 0

    @property
    def n_groups(self) -> int:
        """Honest *n* for rule 4: distinct localities, not sections."""
        return len(self._localities(self.train) | self._localities(self.test))

    @property
    def n_train_groups(self) -> int:
        return len(self._localities(self.train))

    @property
    def n_test_groups(self) -> int:
        return len(self._localities(self.test))

    @staticmethod
    def _localities(units: tuple[Grouped, ...]) -> set[str]:
        return {unit.locality for unit in units}

    def explain(self) -> str:
        """One line, for a log or a slide. Names the honest n and the flattering one."""
        dropped = (
            f", {self.n_dropped_unmeasured} unmeasured dropped" if self.n_dropped_unmeasured else ""
        )
        return (
            f"held out {', '.join(self.held_out)} — "
            f"train {len(self.train)} units from {self.n_train_groups} localities, "
            f"test {len(self.test)} units from {self.n_test_groups} localities. "
            f"Honest n = {self.n_groups} localities, not {len(self.train) + len(self.test)} "
            f"units{dropped}."
        )


def split_by_locality(
    units: tuple[Grouped, ...] | list[Grouped],
    *,
    held_out: tuple[str, ...],
) -> LocalitySplit:
    """Split ``units`` so that whole localities land on one side or the other.

    :param units: sections, patches or grains — anything satisfying :class:`Grouped`. Units
        exposing ``was_measured is False`` are dropped and counted, because a skipped section
        has no pixels and silently leaving it in inflates the denominator.
    :param held_out: locality names for the test side. Must be non-empty, must all be present,
        and must not be every locality there is.
    :raises ValueError: on any of the failure modes rule 2 exists to prevent — a section
        claiming two localities, mixed label provenance, an unrecognised locality name, or a
        split with nothing left to train on.
    """
    if not held_out:
        raise ValueError(
            "held_out is empty. A split with no test localities is not a held-out claim; "
            "name the localities to hold out."
        )

    kept: list[Grouped] = []
    n_dropped = 0
    for unit in units:
        if getattr(unit, "was_measured", True):
            kept.append(unit)
        else:
            n_dropped += 1

    if not kept:
        raise ValueError(
            f"nothing to split: all {n_dropped} units were unmeasured. "
            "Check the bridge's skip reasons before splitting."
        )

    _require_single_provenance(kept)
    _require_one_locality_per_section(kept)

    localities = {unit.locality for unit in kept}
    if len(localities) < 2:
        raise ValueError(
            f"only one locality present ({', '.join(sorted(localities))}). A held-out claim "
            "needs at least two; with one, the test set is either everything or nothing and "
            "the metric describes neither."
        )

    unknown = sorted(set(held_out) - localities)
    if unknown:
        raise ValueError(
            f"held-out locality not present in the data: {', '.join(unknown)}. "
            f"Known localities: {', '.join(sorted(localities))}. A typo here produces an empty "
            "test set and a perfect score."
        )

    train = tuple(unit for unit in kept if unit.locality not in held_out)
    test = tuple(unit for unit in kept if unit.locality in held_out)

    if not train:
        raise ValueError(
            f"holding out {', '.join(sorted(held_out))} leaves nothing to train on — "
            "that is every locality in the data."
        )

    return LocalitySplit(
        train=train,
        test=test,
        held_out=tuple(held_out),
        n_dropped_unmeasured=n_dropped,
    )


def require_locality_disjoint(
    train: tuple[Grouped, ...] | list[Grouped],
    test: tuple[Grouped, ...] | list[Grouped],
) -> None:
    """Refuse a split that shares a locality between train and test.

    The backstop. :func:`split_by_locality` cannot be the only guard, because the failure mode
    is someone building a split by hand — ``train_test_split``, a notebook cell, a shuffled
    list — and never calling the constructor at all. Call this immediately before fitting.

    :raises ValueError: naming every locality that appears on both sides.
    """
    _require_one_locality_per_section([*train, *test])
    shared = sorted({u.locality for u in train} & {u.locality for u in test})
    if shared:
        raise ValueError(
            f"{len(shared)} locality/localities appear on both sides of the split: "
            f"{', '.join(shared)}. This is rule 2 — the metric that comes out of this split "
            "is not a held-out metric, and it will be higher than the honest one."
        )


def _require_single_provenance(units: list[Grouped]) -> None:
    """Same refusal as ``group_by_locality``, for the same reason.

    Ground-truth masks and model predictions carry different error structures; a metric computed
    across a mixture of the two describes neither, and there is no way to recover which is which
    once they are pooled.
    """
    names = {p.name for u in units if (p := getattr(u, "provenance", None)) is not None}
    if len(names) > 1:
        raise ValueError(
            f"mixed label provenance in one split: {', '.join(sorted(names))}. "
            "A metric pooled across hand-drawn masks and model predictions describes neither."
        )


def _require_one_locality_per_section(units: list[Grouped]) -> None:
    """A section came from one place. Two entries claiming otherwise defeat the guard.

    Split on locality all you like: if ``S2_01`` is filed under two localities, the same pixels
    are on both sides of the split and the leak is back, one level down from where the rule
    looks for it. The usual cause is a duplicated or hand-edited manifest.
    """
    seen: dict[str, str] = {}
    for unit in units:
        first = seen.setdefault(unit.section_id, unit.locality)
        if first != unit.locality:
            raise ValueError(
                f"section {unit.section_id} is filed under two localities: {first} and "
                f"{unit.locality}. One section came from one place — fix the manifest before "
                "splitting, or the same pixels land on both sides."
            )
