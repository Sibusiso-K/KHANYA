"""The one remaining item from experiment 007's *Left open* list: does `S3_test_03`'s registered
stack actually look like a properly aligned rotation series, or does its large offset
(-397 px, the biggest of the five sections measured) look like an artefact?

    uv run python experiments/009-s3test03-visual-check/run.py --archive path/to/S3_v2.zip
    uv run python experiments/009-s3test03-visual-check/run.py --archive-dir path/to/extracted

This produces images to *look at*, not a number to trust blindly — a registration search that
converged to a spurious correlation maximum should be visible by eye even where it is not
obvious from `snr_2`/`snr_4` alone: grain edges that jump between frames, a specimen boundary
that does not stay put, or a registered frame that looks less coherent than the naive one it is
supposed to improve on.

**What it writes**, all under ``output/`` (gitignored, same convention as every other
experiment):

- ``frame_00_reference.png`` — the reference frame (angle 0), untouched.
- ``naive_frame_{k}.png`` for a few representative angles — de-rotated about the *image centre*.
- ``registered_frame_{k}.png`` for the same angles — de-rotated about the *estimated* centre.
- ``overlay_naive.png`` / ``overlay_registered.png`` — the reference frame in the red channel and
  a representative de-rotated frame in the green channel, so misalignment shows up as coloured
  fringing at edges rather than requiring the reader to flick between two greyscale images.
- ``registration-check-report.json`` — the numeric side of it (offsets, scores), for the record.
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
    rotate_about,
)

SECTION_SPLIT = "test"
SECTION_STEM = "S3_test_03"

#: Which de-rotated frames to save, chosen to span the series rather than cluster near angle 0
#: where any registration error is smallest.
SAMPLE_ANGLE_INDICES = (1, 10, 30, 60)

SEARCH_DOWNSAMPLE = 8


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
    """Reference in red, ``other`` in green, both clipped to 8-bit — a mis-registered pair shows
    as red/green fringing at every edge; a well-registered pair reads as clean yellow-white.
    """
    height, width = reference.shape
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(reference, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(other, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(path)


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

    reference_small = reference_full[::SEARCH_DOWNSAMPLE, ::SEARCH_DOWNSAMPLE]
    other_small = [frame[::SEARCH_DOWNSAMPLE, ::SEARCH_DOWNSAMPLE] for frame in other_full]

    estimate = estimate_rotation_centre(
        reference_small, other_small, list(other_angles), search_radius=40.0
    )
    full_offset = (
        estimate.offset_xy[0] * SEARCH_DOWNSAMPLE,
        estimate.offset_xy[1] * SEARCH_DOWNSAMPLE,
    )
    height, width = reference_full.shape
    image_centre = (width / 2.0, height / 2.0)
    registered_centre = (image_centre[0] + full_offset[0], image_centre[1] + full_offset[1])

    print(f"estimated offset (full res, x,y): {full_offset}")
    print(f"search score: {estimate.score:.2f} (zero-offset: {estimate.score_at_zero_offset:.2f})")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_png(reference_full, output_dir / "frame_00_reference.png")

    for index in SAMPLE_ANGLE_INDICES:
        if index >= len(other_angles):
            continue
        angle = float(other_angles[index])
        frame = other_full[index]
        naive = rotate_about(frame, -angle, image_centre)
        registered = rotate_about(frame, -angle, registered_centre)
        _save_png(naive, output_dir / f"naive_frame_{index:02d}.png")
        _save_png(registered, output_dir / f"registered_frame_{index:02d}.png")
        print(f"  saved frame index {index} (angle {angle:.1f} deg relative)")

    # One representative mid-series frame for the overlay, so misalignment (which grows with
    # angular separation from the reference) is visible rather than washed out by a near-0 pair.
    # Clamped to the series' actual length, so a short series (a smoke test, a truncated
    # section) degrades gracefully instead of indexing past the end.
    valid_indices = [i for i in SAMPLE_ANGLE_INDICES if i < len(other_angles)]
    overlay_index = valid_indices[len(valid_indices) // 2] if valid_indices else 0
    overlay_angle = float(other_angles[overlay_index])
    overlay_frame = other_full[overlay_index]
    naive_overlay = rotate_about(overlay_frame, -overlay_angle, image_centre)
    registered_overlay = rotate_about(overlay_frame, -overlay_angle, registered_centre)
    _save_overlay(reference_full, naive_overlay, output_dir / "overlay_naive.png")
    _save_overlay(reference_full, registered_overlay, output_dir / "overlay_registered.png")

    report = {
        "section": SECTION_STEM,
        "n_frames": len(frames_meta),
        "offset_xy_full_res": full_offset,
        "search_score": estimate.score,
        "search_score_at_zero_offset": estimate.score_at_zero_offset,
        "overlay_frame_angle_deg": overlay_angle,
        "sample_frame_indices": list(SAMPLE_ANGLE_INDICES),
    }
    (output_dir / "registration-check-report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nwrote images and report to {output_dir}")


if __name__ == "__main__":
    main()
