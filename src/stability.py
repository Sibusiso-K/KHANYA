"""Would the advice survive a change of lighting? If not, do not act on it.

The same polished section, imaged twice under different real conditions, gave a
different recommendation on 5 of 10 LumenStone V1 pairs, and the same held-out
S2 sections darkened by the measured amount changed advice on 8 of 12
(reports/ILLUMINATION-STABILITY-2026-09-15.md). The advisor had no way to know.

This check re-measures the same fields under one fixed re-imaging shift and
refuses a confident recommendation that does not survive it. It has **no tuned
threshold**: the shift is the per-channel median of the real darkening measured
across all ten registered V1 image pairs, and the rule is simply "the action
must not change".

What it is not: a calibration, a robustness guarantee, or a model of every
microscope. It catches one measured kind of variation, and it costs a second
pass over the same fields.
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

UNSTABLE_ACTION = "No recommendation - advice changes under a lighting shift"


def reimaged(image: Image.Image, shift=REIMAGING_SHIFT_RGB) -> Image.Image:
    """The same image as it would read after the measured re-imaging shift."""
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
        f"Measured as imaged, this field says '{original.action}'. Re-measured "
        f"after the lighting shift seen between real re-imagings of the same "
        f"sections (RGB {REIMAGING_SHIFT_RGB[0]:+.0f}/{REIMAGING_SHIFT_RGB[1]:+.0f}/"
        f"{REIMAGING_SHIFT_RGB[2]:+.0f}), it says '{reimaged_action}'. An "
        "instruction that depends on the lamp is not an instruction about the ore, "
        "so none is issued. Standardise illumination or calibrate against a "
        "reflectance standard, then re-measure.",
        original.confidence,
    )
