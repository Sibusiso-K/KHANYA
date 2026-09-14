"""Segmentation's scope guards: locality splits, baselines, and licence choice."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from reefprint.segment.backbone import require_permissive_backbone
from reefprint.trust.baseline import ScoredMetric, TrivialBaselines
from reefprint.trust.split import require_locality_disjoint, split_by_locality


@dataclass(frozen=True)
class Unit:
    section_id: str
    locality: str


def test_splits_are_grouped_by_locality():
    """Rule 2. Patch-level or image-level splits void conformal exchangeability.

    This test must assert that no locality appears on both sides of a split — silently, this
    is the failure that invalidates every metric downstream while every metric still looks fine.
    """
    train = (Unit("a", "North"), Unit("b", "South"))
    test = (Unit("c", "East"),)
    require_locality_disjoint(train, test)
    split = split_by_locality((*train, *test), held_out=("East",))
    assert {unit.locality for unit in split.test} == {"East"}


def test_trivial_baselines_are_reported_alongside_the_model():
    """Rule 3: majority-class AND metadata-only, always.

    The metadata-only baseline doubles as the leakage detector for blind spot 6.
    """
    metric = ScoredMetric(
        name="balanced accuracy",
        value=0.81,
        n=3,
        baselines=TrivialBaselines(majority_class=0.5, metadata_only=0.6),
    )
    summary = metric.summary()
    assert "majority class" in summary
    assert "metadata-only" in summary


def test_backbone_licence_is_permissive():
    """Gauntlet S3. timm (Apache-2.0) and torchvision (BSD-3-Clause) — not DINOv3. Architecture
    and weights are checked separately (SBOM.md's checkpoint table, not this guard).
    """
    require_permissive_backbone()
    require_permissive_backbone("torchvision", "BSD-3-Clause")
    with pytest.raises(ValueError, match=r"DINOv3"):
        require_permissive_backbone("DINOv3", "non-transferable")


def test_backbone_licence_check_is_exact_not_just_the_name():
    """A caller passing the right name with a wrong or invented licence string must be refused
    just as loudly as an unlisted name — this cannot be satisfied by guessing a permissive-
    sounding licence for a backbone actually shipped under a different one.
    """
    with pytest.raises(ValueError, match="torchvision"):
        require_permissive_backbone("torchvision", "MIT")
