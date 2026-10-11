"""Small, provisional previews of completed model forward passes.

The worker passes a source-sized label array after a real tile finishes. In
quick mode that array uses background outside its fields, so a separate union
of completed boxes is essential: those pixels have never been analysed. This
module never treats them as background or includes them in phase fractions.
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import threading
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

MAX_PREVIEW_SIDE = 768
MAX_PREVIEW_BYTES = 2 * 1024 * 1024
MAX_SOURCE_PIXELS = 30_000_000
MAX_COMPLETED_BOXES = 2048
_file_lock = threading.Lock()


def _directory(store: Path, job_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", job_id):
        raise ValueError("Invalid job identifier")
    return Path(store) / "progress" / job_id


class InferenceEvidence:
    """One worker's latest evidence. Arrays stay out of the polling response."""

    def __init__(self, store: Path, job_id: str, image_size, classes, colors, mode: str):
        self.directory = _directory(store, job_id)
        self.job_id = job_id
        self.width, self.height = map(int, image_size)
        if min(self.width, self.height) < 1 or self.width * self.height > MAX_SOURCE_PIXELS:
            raise ValueError("Progress preview image dimensions exceed the supported limit")
        if len(classes) != len(colors) or not classes:
            raise ValueError("Progress phase names and colors must match")
        self.classes, self.colors, self.mode = list(classes), list(colors), mode
        self.covered = np.zeros((self.height, self.width), dtype=bool)
        self.boxes = []
        self.revision = 0
        self.latest = self.empty()

    def empty(self):
        return {"revision": 0, "preview_url": None, "preview_size": None,
                "image_pixels": self.width * self.height, "analysed_pixels": 0,
                "unknown_pixels": self.width * self.height, "invalid_pixels": 0,
                "coverage_fraction": 0.0, "phases": [], "completed_boxes": [],
                "last_tile_confidence": None, "provisional": True,
                "basis": "Completed model pixels only; unanalysed pixels are transparent",
                "aggregation": self.aggregation}

    @property
    def aggregation(self):
        return ("Latest completed tile predictions; final overlap blending is pending"
                if self.mode == "full" else "Completed, non-overlapping native-resolution fields")

    def publish(self, completed: int, total: int, labels, box, confidence):
        if not 1 <= completed <= total <= MAX_COMPLETED_BOXES:
            raise ValueError("Invalid completed tile counts")
        if completed != self.revision + 1:
            raise ValueError("Progress tiles must be published once, in completion order")
        array = np.asarray(labels)
        if array.shape != self.covered.shape or not np.issubdtype(array.dtype, np.integer):
            raise ValueError("Progress labels must be a source-sized integer array")
        if len(box) != 4 or any(int(n) != n for n in box):
            raise ValueError("Invalid completed tile bounding box")
        left, top, right, bottom = map(int, box)
        if not (0 <= left < right <= self.width and 0 <= top < bottom <= self.height):
            raise ValueError("Completed tile falls outside the source image")
        if confidence is not None and not (math.isfinite(confidence) and 0 <= confidence <= 1):
            raise ValueError("Invalid last-tile probability")
        self.covered[top:bottom, left:right] = True
        self.boxes.append([left, top, right, bottom])
        valid = self.covered & (array >= 0) & (array < len(self.classes))
        counts = np.bincount(array[valid], minlength=len(self.classes))
        analysed = int(counts.sum())
        covered = int(np.count_nonzero(self.covered))
        phases = [{"name": name, "color": self.colors[i], "pixels": int(counts[i]),
                   "area_pct": float(counts[i] * 100 / analysed) if analysed else None}
                  for i, name in enumerate(self.classes)]
        size = _preview_size(self.width, self.height)
        # Nearest-neighbour class IDs preserve categorical predictions. The
        # preview is for navigation; all counts above use original pixels.
        small = np.asarray(Image.fromarray(array.astype(np.int32, copy=False)).resize(size, Image.Resampling.NEAREST))
        small_valid = np.asarray(Image.fromarray(valid).resize(size, Image.Resampling.NEAREST))
        rgba = np.zeros((size[1], size[0], 4), dtype=np.uint8)
        for i, color in enumerate(self.colors):
            hit = small_valid & (small == i)
            rgba[hit, :3] = [int(color[k:k + 2], 16) for k in (1, 3, 5)]
            rgba[hit, 3] = 190
        png = io.BytesIO()
        Image.fromarray(rgba).save(png, format="PNG", optimize=True)
        data = png.getvalue()
        if len(data) > MAX_PREVIEW_BYTES:
            raise ValueError("Progress preview exceeds its byte limit")
        self.revision = completed
        snapshot = {"revision": self.revision,
                    "preview_url": f"/api/jobs/{self.job_id}/preview?revision={self.revision}",
                    "preview_size": list(size), "image_pixels": self.width * self.height,
                    "analysed_pixels": analysed, "unknown_pixels": self.width * self.height - covered,
                    "invalid_pixels": covered - analysed,
                    "coverage_fraction": analysed / (self.width * self.height),
                    "phases": phases, "completed_boxes": [b[:] for b in self.boxes],
                    "last_tile_confidence": float(confidence) if confidence is not None else None,
                    "provisional": True, "basis": self.latest["basis"], "aggregation": self.aggregation}
        self.directory.mkdir(parents=True, exist_ok=True)
        # Only the latest bounded PNG and descriptor are retained. Readers use
        # the same lock, so they cannot observe an image/descriptor mismatch.
        with _file_lock:
            temporary = self.directory / (uuid.uuid4().hex + ".tmp")
            try:
                temporary.write_bytes(data)
                os.replace(temporary, self.directory / "latest.png")
                temporary.write_text(json.dumps({"revision": self.revision}), encoding="utf-8")
                os.replace(temporary, self.directory / "latest.json")
            finally:
                temporary.unlink(missing_ok=True)
        self.latest = snapshot
        return snapshot


def _preview_size(width, height):
    scale = min(1.0, MAX_PREVIEW_SIDE / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


def read_preview(store: Path, job_id: str):
    """Called only after the API has found this job in the current tenant."""
    directory = _directory(store, job_id)
    with _file_lock:
        descriptor = json.loads((directory / "latest.json").read_text(encoding="utf-8"))
        with (directory / "latest.png").open("rb") as image:
            data = image.read(MAX_PREVIEW_BYTES + 1)
        if len(data) > MAX_PREVIEW_BYTES:
            raise ValueError("Progress preview exceeds its byte limit")
        return data, int(descriptor["revision"])
