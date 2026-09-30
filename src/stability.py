"""Simulated lighting-perturbation check: an input-sensitivity diagnostic.

The same polished section, imaged twice under different real conditions, gave a
different recommendation on 5 of 10 LumenStone V1 pairs, and the same held-out
S2 sections darkened by the measured amount changed advice on 8 of 12
(reports/ILLUMINATION-STABILITY-2026-09-15.md). The advisor had no way to know.

This check recomputes the same fields on a COPY of the image with a fixed
per-channel RGB offset subtracted. That is a simulated lighting perturbation,
not a second capture. If a confident recommendation changes, it is not issued.
There is no tuned threshold: the offset is the per-channel median of the real
darkening measured across all ten registered V1 image pairs, and the rule is
that the action must not change.

What it is not: an improvement to phase identification, a calibration, a
measurement-system study, or a model of any real microscope change (focus,
glare, colour response). It is one fixed synthetic perturbation. On validation
data it discarded 4 of 5 correct confident calls while catching 5 of 8 wrong
ones, and it costs a second pass over the same fields
(reports/LIGHTING-CHECK-2026-09-30.md).
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from .advisor import ABSTAINING_PREFIXES, Recommendation

# Per-channel median of (b - base) mean pixel value over all ten registered
# LumenStone V1 pairs (001-010), R, G, B. Real re-imaging darkened by 25-37
# levels per pair and more in red than blue (a white-balance shift too), so the
# median is used rather than the extreme.
REIMAGING_SHIFT_RGB = (-34.8, -32.5, -29.6)

UNSTABLE_ACTION = "No recommendation - advice changes under a simulated lighting shift"


def reimaged(image: Image.Image, shift=REIMAGING_SHIFT_RGB) -> Image.Image:
    """A copy of the image with the fixed RGB offset subtracted (simulated, not a capture)."""
    array = np.asarray(image.convert("RGB"), dtype=np.float32) + np.asarray(shift, dtype=np.float32)
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))


def is_abstaining(action: str) -> bool:
    return action.startswith(ABSTAINING_PREFIXES)


def gate(original: Recommendation, reimaged_action: str) -> Recommendation:
    """Keep a confident recommendation only if the re-imaged copy gives the same one.

    An abstention is left as it is: there is no action to protect.
    """
    if is_abstaining(original.action) or reimaged_action == original.action:
        return original
    return Recommendation(
        UNSTABLE_ACTION,
        f"As imaged, this field says '{original.action}'. On a copy of the same "
        f"image with a fixed RGB offset subtracted (R {REIMAGING_SHIFT_RGB[0]:+.1f}, "
        f"G {REIMAGING_SHIFT_RGB[1]:+.1f}, B {REIMAGING_SHIFT_RGB[2]:+.1f}; the median "
        "darkening measured between real re-imagings of LumenStone V1 sections; "
        f"simulated, not a second capture), it says '{reimaged_action}'. Advice that "
        "changes under a simulated lighting change is not issued. Standardise "
        "illumination or calibrate against a reflectance standard, then measure again.",
        original.confidence,
    )
