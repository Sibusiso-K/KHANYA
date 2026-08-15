"""Placeholder — reefprint.segment."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_splits_are_grouped_by_locality():
    """Rule 2. Patch-level or image-level splits void conformal exchangeability.

    This test must assert that no locality appears on both sides of a split — silently, this
    is the failure that invalidates every metric downstream while every metric still looks fine.
    """
    pytest.fail("NOT BUILT — segment: locality-grouped splitting")


def test_trivial_baselines_are_reported_alongside_the_model():
    """Rule 3: majority-class AND metadata-only, always.

    The metadata-only baseline doubles as the leakage detector for blind spot 6.
    """
    pytest.fail("NOT BUILT — segment: trivial baselines")


def test_backbone_licence_is_permissive():
    """Gauntlet S3. timm (Apache-2.0), not DINOv3. Architecture and weights checked separately."""
    pytest.fail("NOT BUILT — segment: backbone selection")
