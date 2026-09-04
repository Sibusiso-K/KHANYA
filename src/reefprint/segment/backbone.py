"""The permitted segmentation backbone declaration."""

from __future__ import annotations

BACKBONE_NAME = "timm"
BACKBONE_LICENSE = "Apache-2.0"

__all__ = ["BACKBONE_LICENSE", "BACKBONE_NAME", "require_permissive_backbone"]


def require_permissive_backbone(name: str = BACKBONE_NAME, license: str = BACKBONE_LICENSE) -> None:
    """Refuse a segmentation backbone that cannot ship to Mintek."""
    if name != "timm" or license != "Apache-2.0":
        raise ValueError(
            f"segmentation backbone {name!r} ({license}) is not the permitted timm/Apache-2.0 stack"
        )
