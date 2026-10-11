"""Persist grain-level evidence tied to one exact segmentation result."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from src import grains


def write_grain_evidence(labels, class_names, phase_fractions, directory: Path) -> dict:
    """Store the report JSON and a lossless 24-bit PNG of the advisor grain IDs."""
    report = grains.grain_report(labels, class_names, phase_fractions=phase_fractions)
    ids = np.asarray(report.grain_map, dtype=np.int64)
    if ids.size and (ids.min() < 0 or ids.max() > 0xFFFFFF):
        raise ValueError("Grain ids cannot be represented losslessly in a 24-bit PNG.")
    packed = ids.astype(np.uint32)
    rgb = np.stack((packed & 255, (packed >> 8) & 255, (packed >> 16) & 255), axis=-1).astype(np.uint8)
    Image.fromarray(rgb, mode="RGB").save(directory / "grain-ids.png", format="PNG")
    payload = {
        "n_grains": report.n_grains,
        "n_payload_grains": report.n_payload_grains,
        "grains": [grain.as_dict() for grain in report.grains],
        "weight_percent": report.weight_percent,
        "association": report.association,
        "liberation_by_size": report.liberation_by_size,
        "microns_per_pixel": report.microns_per_pixel,
    }
    (directory / "grain-report.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    return payload
