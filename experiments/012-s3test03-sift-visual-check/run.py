"""The check `experiments/011-sift-ransac-registration/README.md` says is owed before
SIFT+RANSAC's `S3_test_03` offset becomes a claim: does the registered stack actually look
properly aligned, or does it look like `experiments/009-s3test03-visual-check/`'s grid-search
verdict did — a plausible score, no real alignment?

    uv run python experiments/012-s3test03-sift-visual-check/run.py --archive path/to/S3_v2.zip
    uv run python experiments/012-s3test03-sift-visual-check/run.py --archive-dir path/to/extracted

Directly mirrors `experiments/009`'s method — same section, same sample-frame indices, same
overlay convention (reference in red, de-rotated frame in green; misalignment shows as coloured
fringing, alignment reads as clean yellow-white) — so the two experiments' images are
comparable by eye without translation. The difference: 009 checked one candidate (the grid
search's offset) against the naive baseline; this checks **three** candidates side by side —
naive, the grid search's offset, and SIFT+RANSAC's — because the question this time is not just
"is this offset real" but "which of these two disagreeing offsets is".

**What it writes**, all under ``output/`` (gitignored, same convention as every other
experiment):

- ``frame_00_reference.png`` — the reference frame (angle 0), untouched.
- ``naive_frame_{k}.png`` / ``grid_frame_{k}.png`` / ``sift_frame_{k}.png`` for a few
  representative angles — de-rotated about the image centre, the grid search's estimated centre,
  and SIFT+RANSAC's estimated centre respectively.
- ``overlay_naive.png`` / ``overlay_grid.png`` / ``overlay_sift.png`` — three-way overlay
  comparison at one representative mid-series angle.
- ``visual-check-report.json`` — the numeric side (both offsets, both scores, SIFT+RANSAC's
  per-frame diagnostics), for the record.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(REPO_ROOT / "src"))

from reefprint.acquire.registration import (  # noqa: E402
    estimate_rotation_centre,
    estimate_rotation_centre_sift_ransac,
    rotate_about,
)

SECTION_SPLIT = "test"
SECTION_STEM = "S3_test_03"

#: Same indices as experiment 009, deliberately — spans the series rather than clustering near
#: angle 0, where any registration error is smallest, and keeps the two experiments' images
#: directly comparable frame-for-frame.
SAMPLE_ANGLE_INDICES = (1, 10, 30, 60)

GRID_DOWNSAMPLE = 8
SIFT_DOWNSAMPLE = 2
MAX_SIFT_FRAMES = 10


class _DirArchive:
    """Duck-types :class:`zipfile.ZipFile` against an already-extracted directory. Matches
    ``experiments/007-s3v2-registration/run.py``'s own shim.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._names = [
            str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file()
        ]

    def namelist(self) -> list[str]:
        return self._names

    def open(self, name: str) -> object:
        return (self._root / name).open("rb")


def _load_geometry_experiment() -> ModuleType:
    path = REPO_ROOT / "experiments" / "002-s3v2-geometry" / "run.py"
    spec = importlib.util.spec_from_file_location("s3v2_geometry_experiment", path)
    if spec is None or spec.loader is None:  # pragma: no cover - would mean the file vanished
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _save_png(array: np.ndarray, path: Path) -> None:
    clipped = np.clip(array, 0, 255).astype(np.uint8)
    Image.fromarray(clipped).save(path)


def _save_overlay(reference: np.ndarray, other: np.ndarray, path: Path) -> None:
    """Reference in red, ``other`` in green — matches experiment 009's own convention exactly,
    so a reader can flip between that experiment's overlays and this one's without recalibrating
    what colour means what.
    """
    height, width = reference.shape
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(reference, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(other, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(path)


def _evenly_spaced_indices(count: int, cap: int) -> list[int]:
    if count <= cap:
        return list(range(count))
    return sorted({round(i) for i in np.linspace(0, count - 1, cap)})


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    geometry = _load_geometry_experiment()

    if args.archive is not None:
        archive_cm = zipfile.ZipFile(args.archive)
        archive = archive_cm.__enter__()
    elif args.archive_dir is not None:
        archive_cm = None
        archive = _DirArchive(args.archive_dir)
    else:
        raise SystemExit("pass --archive path/to/S3_v2.zip or --archive-dir path/to/extracted")

    try:
        names = [n for n in archive.namelist() if "__MACOSX" not in n]
        frames_meta = geometry.section_frames(names, SECTION_SPLIT, SECTION_STEM)
        print(f"{SECTION_STEM}: {len(frames_meta)} frames")

        decoded: list[np.ndarray] = []
        angles: list[float] = []
        for degrees, name in frames_meta:
            with archive.open(name) as handle:
                frame = np.array(Image.open(io.BytesIO(handle.read())).convert("L")).astype(
                    np.float32
                )
            decoded.append(frame)
            angles.append(float(degrees))
        stack = np.stack(decoded)
        angles_arr = np.array(angles)
    finally:
        if archive_cm is not None:
            archive_cm.__exit__(None, None, None)

    reference_full = stack[0]
    other_full = stack[1:]
    other_angles = angles_arr[1:] - angles_arr[0]
    other_angles_list = list(other_angles)
    height, width = reference_full.shape
    image_centre = (width / 2.0, height / 2.0)

    # --- Grid search, same recipe as 007/009 ---
    reference_grid = reference_full[::GRID_DOWNSAMPLE, ::GRID_DOWNSAMPLE]
    other_grid = [frame[::GRID_DOWNSAMPLE, ::GRID_DOWNSAMPLE] for frame in other_full]
    grid_estimate = estimate_rotation_centre(
        reference_grid, other_grid, other_angles_list, search_radius=40.0
    )
    grid_offset = (
        grid_estimate.offset_xy[0] * GRID_DOWNSAMPLE,
        grid_estimate.offset_xy[1] * GRID_DOWNSAMPLE,
    )
    grid_centre = (image_centre[0] + grid_offset[0], image_centre[1] + grid_offset[1])
    print(f"grid offset (full res, x,y): {grid_offset}")
    print(
        f"grid score: {grid_estimate.score:.2f} (zero-offset: {grid_estimate.score_at_zero_offset:.2f})"
    )

    # --- SIFT+RANSAC, same recipe as experiment 011 ---
    reference_sift = reference_full[::SIFT_DOWNSAMPLE, ::SIFT_DOWNSAMPLE]
    frame_indices = _evenly_spaced_indices(len(other_full), MAX_SIFT_FRAMES)
    other_sift = [other_full[i][::SIFT_DOWNSAMPLE, ::SIFT_DOWNSAMPLE] for i in frame_indices]
    sift_angles_list = [other_angles_list[i] for i in frame_indices]
    sift_estimate = estimate_rotation_centre_sift_ransac(
        reference_sift, other_sift, sift_angles_list
    )
    if sift_estimate.offset_xy is None:
        raise SystemExit("SIFT+RANSAC found no usable frames on this run — cannot visually check")
    sift_offset = (
        sift_estimate.offset_xy[0] * SIFT_DOWNSAMPLE,
        sift_estimate.offset_xy[1] * SIFT_DOWNSAMPLE,
    )
    sift_centre = (image_centre[0] + sift_offset[0], image_centre[1] + sift_offset[1])
    print(f"sift+ransac offset (full res, x,y): {sift_offset}")
    print(
        f"sift+ransac usable frames: {sift_estimate.usable_frame_count}/{len(sift_estimate.per_frame)}"
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_png(reference_full, output_dir / "frame_00_reference.png")

    for index in SAMPLE_ANGLE_INDICES:
        if index >= len(other_angles):
            continue
        angle = float(other_angles[index])
        frame = other_full[index]
        naive = rotate_about(frame, -angle, image_centre)
        grid_frame = rotate_about(frame, -angle, grid_centre)
        sift_frame = rotate_about(frame, -angle, sift_centre)
        _save_png(naive, output_dir / f"naive_frame_{index:02d}.png")
        _save_png(grid_frame, output_dir / f"grid_frame_{index:02d}.png")
        _save_png(sift_frame, output_dir / f"sift_frame_{index:02d}.png")
        print(f"  saved frame index {index} (angle {angle:.1f} deg relative)")

    valid_indices = [i for i in SAMPLE_ANGLE_INDICES if i < len(other_angles)]
    overlay_index = valid_indices[len(valid_indices) // 2] if valid_indices else 0
    overlay_angle = float(other_angles[overlay_index])
    overlay_frame = other_full[overlay_index]
    naive_overlay = rotate_about(overlay_frame, -overlay_angle, image_centre)
    grid_overlay = rotate_about(overlay_frame, -overlay_angle, grid_centre)
    sift_overlay = rotate_about(overlay_frame, -overlay_angle, sift_centre)
    _save_overlay(reference_full, naive_overlay, output_dir / "overlay_naive.png")
    _save_overlay(reference_full, grid_overlay, output_dir / "overlay_grid.png")
    _save_overlay(reference_full, sift_overlay, output_dir / "overlay_sift.png")

    report = {
        "section": SECTION_STEM,
        "n_frames": len(frames_meta),
        "grid_offset_xy_full_res": grid_offset,
        "grid_score": grid_estimate.score,
        "grid_score_at_zero_offset": grid_estimate.score_at_zero_offset,
        "sift_offset_xy_full_res": sift_offset,
        "sift_usable_frame_count": sift_estimate.usable_frame_count,
        "sift_frame_count": len(sift_estimate.per_frame),
        "sift_per_frame_inlier_counts": [f.inlier_count for f in sift_estimate.per_frame],
        "overlay_frame_angle_deg": overlay_angle,
        "sample_frame_indices": list(SAMPLE_ANGLE_INDICES),
    }
    (output_dir / "visual-check-report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nwrote images and report to {output_dir}")


if __name__ == "__main__":
    main()
