"""Fixes the `S3_test_03` registration search per `experiments/009-s3test03-visual-check/`'s
*What would actually resolve it*: mask out the frame border and background before scoring, so
the objective cannot be won by aligning non-specimen content, and re-run.

    uv run python experiments/010-s3test03-masked-rerun/run.py --archive path/to/S3_v2.zip
    uv run python experiments/010-s3test03-masked-rerun/run.py --archive-dir path/to/extracted

**The mask, and why each part of it is there.** Two independent exclusions, intersected:

1. **A border margin** — pixels within ``BORDER_MARGIN_FRACTION`` of any edge are excluded.
   The previous, unmasked search on this section found an offset of ~397 px on a 3396 px-wide
   frame (session 23); if that number came from border content winning the correlation instead
   of the specimen (session 25's visual-check finding), a margin comfortably larger than that
   removes it from contention regardless of which candidate offset is being scored.
2. **A background brightness threshold** — the darkest ``BACKGROUND_PERCENTILE`` of pixels in
   the *reference* frame are excluded. Reflected-light ore microscopy's own convention
   (CLAUDE.md's physics table: resin/background R ~ 4.5-5%, every mineral phase brighter) makes
   low brightness a reasonable, non-mineralogical proxy for "not specimen" — this is a
   registration engineering choice, not a mineral classification (Rule 6 governs classifying
   *which* mineral a pixel is, not excluding the darkest pixels from a correlation objective).
   The threshold is computed once, from the reference frame only, so it cannot change during
   the search the way a per-candidate mask could be gamed by it.

This does not re-derive the mask from first principles for every archive — it is a fix for this
one section, checked here, not a general-purpose foreground detector promoted to the module.
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
    inscribed_region_mask,
    rotate_about,
)
from reefprint.polarim.geometry import harmonic_signature  # noqa: E402

SECTION_SPLIT = "test"
SECTION_STEM = "S3_test_03"

SEARCH_DOWNSAMPLE = 8
BORDER_MARGIN_FRACTION = 0.20
BACKGROUND_PERCENTILE = 15.0

#: The offset the earlier, unmasked search found (session 23) — kept here as a stated prior
#: result to compare against, not recomputed each run.
PREVIOUS_OFFSET_XY = (-397.25651577503425, 40.82304526748971)
PREVIOUS_VERDICT = {"snr_2": 3.194099337309768, "snr_4": 5.288888879396182, "verdict": "FOURTH"}
PREVIOUS_NAIVE = {"snr_2": 9.350294830486483, "snr_4": 2.7758807045080824, "verdict": "SECOND"}


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


def build_roi_mask(reference: np.ndarray) -> np.ndarray:
    """Border margin AND background-brightness exclusion, intersected. See module docstring."""
    height, width = reference.shape
    margin_y = round(height * BORDER_MARGIN_FRACTION)
    margin_x = round(width * BORDER_MARGIN_FRACTION)
    border_mask = np.zeros(reference.shape, dtype=bool)
    border_mask[margin_y : height - margin_y, margin_x : width - margin_x] = True

    threshold = np.percentile(reference, BACKGROUND_PERCENTILE)
    brightness_mask = reference > threshold

    return border_mask & brightness_mask


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("masked-rerun-report.json"))
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

    roi_mask_small = build_roi_mask(reference_small)
    print(
        f"ROI mask (downsampled): {roi_mask_small.sum()} / {roi_mask_small.size} pixels kept "
        f"({100.0 * roi_mask_small.mean():.1f}%)"
    )

    estimate_unmasked = estimate_rotation_centre(
        reference_small, other_small, list(other_angles), search_radius=40.0
    )
    estimate_masked = estimate_rotation_centre(
        reference_small,
        other_small,
        list(other_angles),
        search_radius=40.0,
        roi_mask=roi_mask_small,
    )

    print(f"unmasked search (this run): offset {estimate_unmasked.offset_xy}")
    print(f"masked search (this run):   offset {estimate_masked.offset_xy}")
    print(f"previous run (session 23):  offset {PREVIOUS_OFFSET_XY}")

    full_offset_masked = (
        estimate_masked.offset_xy[0] * SEARCH_DOWNSAMPLE,
        estimate_masked.offset_xy[1] * SEARCH_DOWNSAMPLE,
    )
    height, width = reference_full.shape
    image_centre = (width / 2.0, height / 2.0)
    masked_centre = (
        image_centre[0] + full_offset_masked[0],
        image_centre[1] + full_offset_masked[1],
    )
    naive_centre = image_centre

    def build_stack(centre_xy: tuple[float, float]) -> np.ndarray:
        registered = [reference_full]
        for angle, frame in zip(other_angles, other_full, strict=True):
            registered.append(rotate_about(frame, -angle, centre_xy))
        return np.stack(registered)

    naive_stack = build_stack(naive_centre)
    masked_stack = build_stack(masked_centre)
    inscribed_naive = inscribed_region_mask(reference_full.shape, naive_centre)
    inscribed_masked = inscribed_region_mask(reference_full.shape, masked_centre)

    angles_rad = np.deg2rad(angles_arr - angles_arr[0])
    naive_signature = harmonic_signature(naive_stack[:, inscribed_naive], angles_rad)
    masked_signature = harmonic_signature(masked_stack[:, inscribed_masked], angles_rad)

    print(
        f"\nnaive (this run):  verdict={naive_signature.verdict.name} "
        f"snr_2={naive_signature.snr_2:.2f} snr_4={naive_signature.snr_4:.2f}"
    )
    print(
        f"masked-registered: verdict={masked_signature.verdict.name} "
        f"snr_2={masked_signature.snr_2:.2f} snr_4={masked_signature.snr_4:.2f} "
        f"offset_full_res={full_offset_masked}"
    )
    print(
        f"previous unmasked-registered (session 23): verdict={PREVIOUS_VERDICT['verdict']} "
        f"snr_2={PREVIOUS_VERDICT['snr_2']:.2f} snr_4={PREVIOUS_VERDICT['snr_4']:.2f}"
    )

    report = {
        "section": SECTION_STEM,
        "roi_mask_kept_fraction": float(roi_mask_small.mean()),
        "unmasked_offset_downsampled": estimate_unmasked.offset_xy,
        "masked_offset_downsampled": estimate_masked.offset_xy,
        "masked_offset_full_res": full_offset_masked,
        "previous_offset_full_res": PREVIOUS_OFFSET_XY,
        "naive_this_run": {
            "verdict": naive_signature.verdict.name,
            "snr_2": naive_signature.snr_2,
            "snr_4": naive_signature.snr_4,
        },
        "masked_registered_this_run": {
            "verdict": masked_signature.verdict.name,
            "snr_2": masked_signature.snr_2,
            "snr_4": masked_signature.snr_4,
        },
        "previous_unmasked_registered": PREVIOUS_VERDICT,
        "previous_naive": PREVIOUS_NAIVE,
    }
    args.output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {args.output}")


if __name__ == "__main__":
    main()
