"""The permitted segmentation backbone declaration.

**Widened 2026-09-15** (Workstream F, `docs/10-2026-09-14-literature-and-brief-plan.md`). This
guard originally permitted only ``timm``/Apache-2.0 — but KHANYA's actual segmentation model
(``khanya/main:src/segmentation/model.py``) is ``torchvision.models.segmentation.deeplabv3_resnet50``,
which the guard would have refused had anyone ever called it against the real build. A guard that
contradicts the thing it is meant to check is worse than no guard: it either goes uncalled (and
nobody notices it is wrong) or it fails on legitimate code and gets bypassed. ``torchvision`` is
BSD-3-Clause and is added to the permitted set for that reason, not because the underlying
checkpoint chain is fully cleared — see the SBOM caveat below, which this module deliberately does
not paper over.

**What this checks, and what it does not.** This function checks the *library and architecture
code's* licence — the thing Rule 7 and gauntlet finding S3 are about (copyleft code linked into an
assigned deliverable). It says nothing about a specific *trained checkpoint's* permission chain,
which is a separate question (see `SBOM.md`'s checkpoint table) — a permissively-licensed
architecture can still load weights trained on data with unclear redistribution terms. DINOv3 is
still rejected here for a licence reason (non-transferable, no patent grant); a checkpoint's
provenance is rejected, if it is, for a different reason entirely, and belongs in the SBOM's
checkpoint row, not in this function.
"""

from __future__ import annotations

BACKBONE_NAME = "timm"
BACKBONE_LICENSE = "Apache-2.0"

#: Every (architecture library, licence) pair this project will ship. Keyed by name so a caller
#: gets one unambiguous licence to check against, rather than a list that could contain the same
#: name twice under two different licences by accident.
PERMITTED_BACKBONES: dict[str, str] = {
    "timm": "Apache-2.0",
    # torchvision's segmentation models (`deeplabv3_resnet50`, KHANYA's actual architecture) —
    # the library and architecture code are BSD-3-Clause. The DEFAULT checkpoint's own training
    # chain (COCO subset -> ImageNet-pretrained ResNet50 backbone) is a separate, not fully
    # cleared question — SBOM.md's checkpoint table, not this guard.
    "torchvision": "BSD-3-Clause",
}

__all__ = [
    "BACKBONE_LICENSE",
    "BACKBONE_NAME",
    "PERMITTED_BACKBONES",
    "require_permissive_backbone",
]


def require_permissive_backbone(name: str = BACKBONE_NAME, license: str = BACKBONE_LICENSE) -> None:
    """Refuse a segmentation backbone that cannot ship to Mintek.

    Checks ``name`` against :data:`PERMITTED_BACKBONES` and requires the *exact* licence on
    record for it — passing the right name with a wrong or invented licence string is refused
    just as loudly as an unlisted name, so this cannot be satisfied by guessing a licence that
    happens to sound permissive.
    """
    if PERMITTED_BACKBONES.get(name) != license:
        raise ValueError(
            f"segmentation backbone {name!r} ({license}) is not one of the permitted backbones: "
            f"{PERMITTED_BACKBONES}"
        )
