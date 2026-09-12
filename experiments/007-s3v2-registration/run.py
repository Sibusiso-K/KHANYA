"""Leg (b), for real: does registering S3 v2's frames let a harmonic clear its detection floor?

Runs on Kaggle, not locally — a full section's frame stack needs ~5 GB once constructed
(``experiments/003-s3v2-extinction/run.py``'s own docstring), and this project's local machine
does not reliably have that free. See ``kernel-metadata.json`` in this directory for the push
command; this script is the kernel's entry point once mounted there.

**What this measures.** Session 17's finding: naive centred de-rotation does not register S3 v2's
frames, because the rotation axis is off-image-centre and varies by section. This script:

1. Loads each section's real frame stack and its nominal per-frame angles (from filenames,
   ``experiments/002-s3v2-geometry/run.py::section_frames`` — never estimated, always read).
2. Estimates the true rotation-centre offset with
   :func:`reefprint.acquire.registration.estimate_rotation_centre`, at a **downsampled**
   resolution — the search itself does not need full resolution, only the final registered
   stack does, and estimating at low resolution keeps this affordable even off Kaggle if it ever
   needs to be.
3. Builds two stacks per section: the **naive** one (every frame de-rotated about the image
   centre by its nominal angle — what every prior run on this archive actually did) and the
   **registered** one (de-rotated about the *estimated* true centre), both restricted to the
   region :func:`~reefprint.acquire.registration.inscribed_region_mask` guarantees is real
   content in every frame.
4. Runs :func:`reefprint.polarim.geometry.harmonic_signature` on both, and reports the
   comparison. **This is the actual leg-(b) result** — the one this project has not had since
   N3's withdrawal.

**What this does not claim before it runs.** Registering the frames does not by itself say
which geometry the archive is — `harmonic_signature`'s verdict on the *registered* stack is
the answer to that, not an assumption going in. And a registered `NEITHER` still means the same
thing session 17's finding already established: no harmonic clears the floor, on data that can
now at least be trusted to represent the same physical points across frames.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import zipfile
from collections.abc import Callable
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

#: Sections to attempt unless overridden. Matches experiment 002's own default so results are
#: comparable to that run's per-section table.
DEFAULT_SECTIONS = 6

#: Downsample factor for the registration SEARCH only (not for the final harmonic check, which
#: runs on the full-resolution registered stack restricted to the inscribed region). A coarse
#: search is validated to sub-pixel accuracy on synthetic data at this kind of resolution —
#: see tests/test_registration.py — and running the search at full resolution would cost dozens
#: of full-frame warps per section for no accuracy this problem needs.
SEARCH_DOWNSAMPLE = 8


class _DirArchive:
    """Duck-types :class:`zipfile.ZipFile`'s ``namelist``/``open`` against an already-extracted
    directory — Kaggle auto-extracts an uploaded zip dataset rather than keeping it as one
    archive (found in session 16f, `docs/BUILDLOG.md`), so the loader written for a real zip
    needs this shim to run unchanged on the mounted dataset.
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


def _find_dataset_root(base: Path, fragment: str) -> Path:
    """A Kaggle mount nests one level deeper than the naive `/kaggle/input/<slug>` guess
    (session 16f) — search for a directory whose path contains ``fragment`` rather than assume
    an exact layout.
    """
    for candidate in base.rglob("*"):
        if candidate.is_dir() and fragment in str(candidate).replace("\\", "/"):
            return candidate
    raise SystemExit(f"could not find a directory matching {fragment!r} under {base}")


def load_section(
    archive: object,
    names: list[str],
    split: str,
    stem: str,
    section_frames_fn: Callable[[list[str], str, str], list[tuple[int, str]]],
) -> tuple[np.ndarray, np.ndarray] | str:
    """Return ``(stack, angles_deg)`` for one section, full resolution, float32 — or a ``str``
    reason the section cannot be used. ``stack`` is ``(n_angles, height, width)``.
    """
    frames_meta = section_frames_fn(names, split, stem)
    if len(frames_meta) < 3:
        return f"only {len(frames_meta)} rotation frames"

    decoded: list[np.ndarray] = []
    angles: list[float] = []
    reference_shape: tuple[int, int] | None = None
    for degrees, name in frames_meta:
        with archive.open(name) as handle:
            frame = np.array(Image.open(io.BytesIO(handle.read())).convert("L")).astype(np.float32)
        if reference_shape is None:
            reference_shape = frame.shape
        elif frame.shape != reference_shape:
            return f"frame {name.rsplit('/', 1)[-1]} shape {frame.shape} != {reference_shape}"
        decoded.append(frame)
        angles.append(float(degrees))

    return np.stack(decoded), np.array(angles)


def _downsample(stack: np.ndarray, factor: int) -> list[np.ndarray]:
    return [frame[::factor, ::factor] for frame in stack]


def register_and_measure(stack: np.ndarray, angles_deg: np.ndarray) -> dict[str, object]:
    """The comparison this experiment exists to produce: naive vs registered, on one section."""
    reference_full = stack[0]
    other_full = stack[1:]
    other_angles = angles_deg[1:] - angles_deg[0]

    reference_small = reference_full[::SEARCH_DOWNSAMPLE, ::SEARCH_DOWNSAMPLE]
    other_small = _downsample(other_full, SEARCH_DOWNSAMPLE)

    estimate = estimate_rotation_centre(
        reference_small, other_small, list(other_angles), search_radius=40.0
    )
    # Scale the offset found at low resolution back up to full resolution.
    full_offset = (
        estimate.offset_xy[0] * SEARCH_DOWNSAMPLE,
        estimate.offset_xy[1] * SEARCH_DOWNSAMPLE,
    )

    height, width = reference_full.shape
    image_centre = (width / 2.0, height / 2.0)
    registered_centre = (image_centre[0] + full_offset[0], image_centre[1] + full_offset[1])

    def build_stack(centre_xy: tuple[float, float]) -> np.ndarray:
        registered = [reference_full]
        for angle, frame in zip(other_angles, other_full, strict=True):
            registered.append(rotate_about(frame, -angle, centre_xy))
        return np.stack(registered)

    naive_stack = build_stack(image_centre)
    registered_stack = build_stack(registered_centre)

    inscribed_naive = inscribed_region_mask(reference_full.shape, image_centre)
    inscribed_registered = inscribed_region_mask(reference_full.shape, registered_centre)

    angles_rad = np.deg2rad(angles_deg - angles_deg[0])

    naive_samples = naive_stack[:, inscribed_naive]
    registered_samples = registered_stack[:, inscribed_registered]

    naive_signature = harmonic_signature(naive_samples, angles_rad)
    registered_signature = harmonic_signature(registered_samples, angles_rad)

    return {
        "offset_xy_full_res": full_offset,
        "search_score": estimate.score,
        "search_score_at_zero_offset": estimate.score_at_zero_offset,
        "improves_on_naive": estimate.improves_on_naive_derotation,
        "naive": {
            "verdict": naive_signature.verdict.value,
            "snr_2": naive_signature.snr_2,
            "snr_4": naive_signature.snr_4,
        },
        "registered": {
            "verdict": registered_signature.verdict.value,
            "snr_2": registered_signature.snr_2,
            "snr_4": registered_signature.snr_4,
        },
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=None, help="path to S3_v2.zip")
    parser.add_argument(
        "--archive-dir", type=Path, default=None, help="path to an already-extracted S3_v2 dir"
    )
    parser.add_argument("--sections", type=int, default=DEFAULT_SECTIONS)
    parser.add_argument("--output", type=Path, default=Path("registration-report.json"))
    args = parser.parse_args()

    geometry_experiment = _load_geometry_experiment()

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
        sections = geometry_experiment.list_sections(names)
        print(
            f"{len(sections)} sections in archive; attempting {min(args.sections, len(sections))}\n"
        )

        results: dict[str, object] = {}
        for split, stem in sections[: args.sections]:
            outcome = load_section(archive, names, split, stem, geometry_experiment.section_frames)
            if isinstance(outcome, str):
                print(f"{split}/{stem}: SKIPPED ({outcome})")
                results[f"{split}/{stem}"] = {"skipped": outcome}
                continue
            stack, angles_deg = outcome
            print(f"{split}/{stem}: {stack.shape[0]} frames, {stack.shape[1]}x{stack.shape[2]}")
            comparison = register_and_measure(stack, angles_deg)
            results[f"{split}/{stem}"] = comparison
            print(
                f"  naive:      {comparison['naive']['verdict']:8s} "
                f"snr_2={comparison['naive']['snr_2']:.2f} snr_4={comparison['naive']['snr_4']:.2f}"
            )
            print(
                f"  registered: {comparison['registered']['verdict']:8s} "
                f"snr_2={comparison['registered']['snr_2']:.2f} "
                f"snr_4={comparison['registered']['snr_4']:.2f} "
                f"(offset {comparison['offset_xy_full_res']}, "
                f"search improved: {comparison['improves_on_naive']})"
            )
    finally:
        if archive_cm is not None:
            archive_cm.__exit__(None, None, None)

    args.output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {args.output}")


if __name__ == "__main__":
    main()
