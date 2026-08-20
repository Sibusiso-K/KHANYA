"""Rule 2, made structural: split by locality, never by patch or image.

The rule's own wording is *"will silently invalidate every metric"*. Silently is the whole
problem — a patch-level split does not raise, does not warn, and returns a *better* number than
the honest split, so the failure is indistinguishable from success right up until someone else
tries to reproduce it. These tests pin the guard that turns that into a refusal.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from reefprint.acquire.series import RotationGeometry
from reefprint.bridge.measure import SectionMeasurement
from reefprint.bridge.section import LabelProvenance
from reefprint.trust.split import (
    LocalitySplit,
    require_locality_disjoint,
    split_by_locality,
)


def measurement(
    section_id: str,
    locality: str,
    *,
    skipped: str | None = None,
    provenance: LabelProvenance = LabelProvenance.GROUND_TRUTH,
) -> SectionMeasurement:
    """A measured section, stripped to the fields a split actually reads."""
    return SectionMeasurement(
        section_id=section_id,
        locality=locality,
        provenance=provenance,
        geometry=RotationGeometry.ANALYSER,
        n_angles=36,
        per_mineral=(),
        n_pixels_measured=0 if skipped else 5000,
        n_pixels_unlabelled=0,
        skipped=skipped,
    )


THREE_LOCALITIES = (
    measurement("S2_01", "Norilsk"),
    measurement("S2_02", "Norilsk"),
    measurement("S3_01", "Dalnegorsk"),
    measurement("S3_02", "Dalnegorsk"),
    measurement("IO_01", "Bailadila"),
    measurement("IO_02", "Bailadila"),
)


# --------------------------------------------------------------------------------------
# The core refusal
# --------------------------------------------------------------------------------------


def test_a_locality_on_both_sides_of_a_split_is_refused():
    """The failure rule 2 exists to prevent, stated as an assertion.

    A hand-built split is the route around :func:`split_by_locality`, so the backstop has to
    catch it independently.
    """
    train = (measurement("S2_01", "Norilsk"), measurement("S3_01", "Dalnegorsk"))
    test = (measurement("S2_02", "Norilsk"),)

    with pytest.raises(ValueError, match="Norilsk"):
        require_locality_disjoint(train, test)


def test_a_disjoint_split_passes_the_backstop():
    train = (measurement("S2_01", "Norilsk"),)
    test = (measurement("S3_01", "Dalnegorsk"),)

    require_locality_disjoint(train, test)  # must not raise


def test_the_same_section_under_two_localities_is_refused():
    """One polished section cannot have come from two places.

    This is the tell for a mislabelled or duplicated manifest, and it defeats the locality
    guard from underneath: split on locality all you like, the same pixels are on both sides.
    """
    units = (
        measurement("S2_01", "Norilsk"),
        measurement("S2_01", "Dalnegorsk"),
    )

    with pytest.raises(ValueError, match="S2_01"):
        split_by_locality(units, held_out=("Dalnegorsk",))


# --------------------------------------------------------------------------------------
# The constructor
# --------------------------------------------------------------------------------------


def test_splitting_by_locality_keeps_whole_localities_on_one_side():
    split = split_by_locality(THREE_LOCALITIES, held_out=("Dalnegorsk",))

    assert {m.locality for m in split.train} == {"Norilsk", "Bailadila"}
    assert {m.locality for m in split.test} == {"Dalnegorsk"}
    assert isinstance(split, LocalitySplit)


def test_holding_out_a_locality_that_is_not_present_is_refused():
    """A typo in a locality name otherwise produces an empty test set and a perfect score."""
    with pytest.raises(ValueError, match="Norilsk-2"):
        split_by_locality(THREE_LOCALITIES, held_out=("Norilsk-2",))


def test_holding_out_every_locality_leaves_nothing_to_train_on():
    with pytest.raises(ValueError, match="nothing to train"):
        split_by_locality(THREE_LOCALITIES, held_out=("Norilsk", "Dalnegorsk", "Bailadila"))


def test_holding_out_nothing_is_refused():
    with pytest.raises(ValueError, match="empty"):
        split_by_locality(THREE_LOCALITIES, held_out=())


def test_mixed_label_provenance_is_refused_in_a_split_too():
    """Same reason ``group_by_locality`` refuses it: the mixture describes neither."""
    units = (
        measurement("S2_01", "Norilsk"),
        measurement("S3_01", "Dalnegorsk", provenance=LabelProvenance.PREDICTED),
    )

    with pytest.raises(ValueError, match=r"GROUND_TRUTH|PREDICTED"):
        split_by_locality(units, held_out=("Dalnegorsk",))


def test_unmeasured_sections_are_dropped_and_counted():
    """A skipped section has no pixels. Silently leaving it in inflates the denominator."""
    units = (*THREE_LOCALITIES, measurement("S2_03", "Norilsk", skipped="shape mismatch"))

    split = split_by_locality(units, held_out=("Dalnegorsk",))

    assert split.n_dropped_unmeasured == 1
    assert all(m.was_measured for m in split.train)


# --------------------------------------------------------------------------------------
# Honest n
# --------------------------------------------------------------------------------------


def test_honest_n_is_the_number_of_localities_not_the_number_of_sections():
    """Rule 4 depends on this. Six sections from three localities is n = 3, not n = 6.

    Quoting n = 6 halves every confidence interval on the slide, which is the arithmetic a
    judge can redo in their head.
    """
    split = split_by_locality(THREE_LOCALITIES, held_out=("Dalnegorsk",))

    assert split.n_groups == 3
    assert split.n_train_groups == 2
    assert split.n_test_groups == 1
    assert len(split.train) == 4  # sections, deliberately a different number


def test_a_single_locality_cannot_support_a_held_out_claim():
    units = (measurement("S2_01", "Norilsk"), measurement("S2_02", "Norilsk"))

    with pytest.raises(ValueError, match="one locality"):
        split_by_locality(units, held_out=("Norilsk",))


# --------------------------------------------------------------------------------------
# The number that justifies the guard
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Patch:
    """One patch cut from a section. What a patch-level split shuffles."""

    section_id: str
    locality: str
    x: float
    y: float


def synthetic_patches(seed: int = 20260820) -> tuple[Patch, ...]:
    """Sections with a strong per-section signature, patches cut from each.

    The feature carries the *section's* identity and nothing else — there is no transferable
    signal to learn. Any model that scores well here has memorised which section a patch came
    from, which is precisely what a patch-level split lets it do.
    """
    rng = np.random.default_rng(seed)
    patches = []
    for locality_index in range(6):
        for section_index in range(4):
            signature = rng.normal(0.0, 1.0)
            for _ in range(8):
                patches.append(
                    Patch(
                        section_id=f"L{locality_index}_S{section_index}",
                        locality=f"locality_{locality_index}",
                        x=signature + rng.normal(0.0, 0.01),
                        y=signature,
                    )
                )
    return tuple(patches)


def nearest_neighbour_error(train: tuple[Patch, ...], test: tuple[Patch, ...]) -> float:
    """Mean absolute error of a 1-NN predictor. The simplest model that can memorise."""
    train_x = np.array([p.x for p in train])
    train_y = np.array([p.y for p in train])
    test_x = np.array([p.x for p in test])
    test_y = np.array([p.y for p in test])
    nearest = np.abs(test_x[:, None] - train_x[None, :]).argmin(axis=1)
    return float(np.abs(train_y[nearest] - test_y).mean())


def test_a_patch_level_split_reports_a_far_better_score_than_the_honest_one():
    """The measured version of "silently invalidate every metric".

    Same data, same model, two splits. The patch split is the one that looks good.
    """
    patches = synthetic_patches()
    rng = np.random.default_rng(1)

    shuffled = list(patches)
    rng.shuffle(shuffled)
    cut = len(shuffled) // 2
    patch_split_error = nearest_neighbour_error(tuple(shuffled[:cut]), tuple(shuffled[cut:]))

    honest = split_by_locality(patches, held_out=("locality_4", "locality_5"))
    locality_split_error = nearest_neighbour_error(honest.train, honest.test)

    assert patch_split_error < locality_split_error / 10, (
        f"patch split MAE {patch_split_error:.4f} vs locality split MAE "
        f"{locality_split_error:.4f} — the leak should be an order of magnitude"
    )


def test_the_guard_catches_the_patch_split_that_produced_that_score():
    """And the split that produced the flattering number is refusable, not merely regrettable."""
    patches = synthetic_patches()
    rng = np.random.default_rng(1)
    shuffled = list(patches)
    rng.shuffle(shuffled)
    cut = len(shuffled) // 2

    with pytest.raises(ValueError, match="locality_"):
        require_locality_disjoint(tuple(shuffled[:cut]), tuple(shuffled[cut:]))
