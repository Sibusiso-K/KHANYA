"""Rule 10, applied to the case that motivated it: does the published SIFT+RANSAC registration
method (Korshunov et al. 2025) do any better than the bespoke grid search on the same five real
S3 v2 sections `experiments/010` found the grid search non-reproducible on?

    uv run python experiments/011-sift-ransac-registration/run.py --archive path/to/S3_v2.zip

**Not a replacement experiment — a comparison.** Both estimators run on the same decoded frame
stacks, in the same process, so any difference in their offsets is a difference between the
methods, not between runs. Per CLAUDE.md's determinism discipline: before any SIFT+RANSAC offset
is trusted, this script runs that estimator **twice** on real data and asserts the result is
bit-for-bit identical — the same check that would have caught the grid search's
non-reproducibility immediately, had it existed before session 26.

**Cost-controlled after the first version of this script ran on Kaggle for hours without
finishing** (see `MAX_SIFT_FRAMES`'s docstring): the determinism check runs on only the *first*
usable section, not every section (determinism is a property of the code and its seeded RNG, not
something that should vary section to section), and SIFT+RANSAC itself runs on an evenly-spaced
subsample of at most `MAX_SIFT_FRAMES` frames per section, not every frame in a rotation series
that can run to 71 frames.

**What this measures, precisely.**

1. Loads each section's real frame stack and nominal per-frame angles, exactly as
   `experiments/007-s3v2-registration/run.py` does (imported, not duplicated).
2. Runs the existing grid-search estimator (`estimate_rotation_centre`) at the same downsample
   factor as 007 (`GRID_DOWNSAMPLE = 8`), for direct comparability with that experiment's numbers,
   on every "other" frame — unchanged from 007, since that part was never the cost problem.
3. Runs the SIFT+RANSAC estimator (`estimate_rotation_centre_sift_ransac`) at its own, lighter
   downsample (`SIFT_DOWNSAMPLE = 2` — see that constant's comment for why it needs to differ) on
   at most `MAX_SIFT_FRAMES` frames, evenly spaced across the rotation range; on the first usable
   section only, **twice**, recording whether the two calls agree bit-for-bit.
4. Builds a registered stack — over *every* frame in the section, regardless of how many fed the
   search — under each estimator's offset (plus the naive, zero-offset baseline), and reports
   `harmonic_signature`'s verdict on all three, so a judgement about which method (if either) is
   trustworthy can be made from the actual downstream answer, not just the offset.

**What this does not claim before it runs.** Agreement between the two estimators would be
evidence neither is fooled by a section-specific artefact; disagreement does not by itself say
which one is right — `experiments/009`'s visual check is still the standard for that, and should
be re-run against whichever estimator's offset (if either) looks trustworthy here.
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
    estimate_rotation_centre_sift_ransac,
    inscribed_region_mask,
    rotate_about,
)
from reefprint.polarim.geometry import harmonic_signature  # noqa: E402

#: Matches experiment 002's and 007's own default so results are comparable to those runs'
#: per-section tables.
DEFAULT_SECTIONS = 6

#: Same downsample as experiment 007, for the grid-search estimator. Its per-candidate cost
#: (hundreds of full-frame warps per section) makes a coarse downsample necessary.
GRID_DOWNSAMPLE = 8

#: A lighter downsample for SIFT+RANSAC, deliberately different from ``GRID_DOWNSAMPLE``. SIFT's
#: cost is one detect-and-extract pass per frame, not per candidate, so it does not need the same
#: aggressive reduction — and checked directly on a synthetic field at this project's scale, it
#: needs the lighter touch: at downsample 8, matched keypoints per frame dropped to 0-3 (below
#: ``min_matches``, every frame reported unusable); at downsample 2 on the same synthetic field,
#: 23 of 24 frames were usable and recovered a known offset to within ~0.5px after rescaling. Real
#: mineral texture is richer than the synthetic blobs this was checked against, so this is a
#: conservative choice, not an optimistic one.
SIFT_DOWNSAMPLE = 2

#: A cap on how many "other" frames SIFT+RANSAC processes per section, evenly subsampled across
#: the full rotation range. **Added after the first Kaggle run of this experiment ran for hours
#: without completing** (docs/BUILDLOG.md, this session) — SIFT at SIFT_DOWNSAMPLE=2 on a section
#: with up to 71 other frames, computed TWICE (the determinism check) across up to 12 attempted
#: sections, is the actual cost driver: `estimate_rotation_centre_sift_ransac` runs SIFT fresh on
#: every frame with no caching between calls, so one section's determinism check alone was up to
#: ~140 full detect-and-extract-and-match passes at ~2 megapixels each. The per-frame estimator
#: does not need every frame to characterise its own accuracy or determinism — a subsample spread
#: across the rotation range exercises the same code path at a small fraction of the cost.
MAX_SIFT_FRAMES = 10


class _DirArchive:
    """Duck-types :class:`zipfile.ZipFile` against an already-extracted directory — Kaggle
    auto-extracts an uploaded zip dataset (found in session 16f, `docs/BUILDLOG.md`), same shim
    as `experiments/007-s3v2-registration/run.py`.
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


def load_section(
    archive: object,
    names: list[str],
    split: str,
    stem: str,
    section_frames_fn: Callable[[list[str], str, str], list[tuple[int, str]]],
) -> tuple[np.ndarray, np.ndarray] | str:
    """Same contract as `experiments/007-s3v2-registration/run.py::load_section` — returns
    ``(stack, angles_deg)`` full resolution, float32, or a ``str`` reason it cannot be used.
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


def _evenly_spaced_indices(count: int, cap: int) -> list[int]:
    """Indices spanning ``range(count)`` at even spacing, capped at ``cap`` entries — a
    deterministic subsample (``np.linspace`` rounded), not a random one, so the same section
    always selects the same frames regardless of ``MAX_SIFT_FRAMES``'s exact value at the time.
    """
    if count <= cap:
        return list(range(count))
    return sorted({round(i) for i in np.linspace(0, count - 1, cap)})


def _harmonic_for_offset(
    reference_full: np.ndarray,
    other_full: np.ndarray,
    other_angles: np.ndarray,
    angles_rad: np.ndarray,
    offset_xy: tuple[float, float] | None,
) -> dict[str, object] | None:
    if offset_xy is None:
        return None
    height, width = reference_full.shape
    centre = (width / 2.0 + offset_xy[0], height / 2.0 + offset_xy[1])
    registered = [reference_full]
    for angle, frame in zip(other_angles, other_full, strict=True):
        registered.append(rotate_about(frame, -angle, centre))
    stack_reg = np.stack(registered)
    inscribed = inscribed_region_mask(reference_full.shape, centre)
    samples = stack_reg[:, inscribed]
    signature = harmonic_signature(samples, angles_rad)
    return {"verdict": signature.verdict.value, "snr_2": signature.snr_2, "snr_4": signature.snr_4}


def compare_methods(
    stack: np.ndarray, angles_deg: np.ndarray, *, check_determinism: bool
) -> dict[str, object]:
    """The comparison this experiment exists to produce: grid search vs SIFT+RANSAC vs naive, on
    one section.

    :param check_determinism: if true, runs the SIFT+RANSAC estimator **twice** on this section
        and asserts bit-for-bit agreement before trusting its offset — the real-data check this
        experiment exists to make. Costly (see ``MAX_SIFT_FRAMES``'s docstring), so ``main`` runs
        it on only the first usable section: determinism is a property of the code and its seeded
        RNG, not something that should vary section to section, so one real-data confirmation is
        the evidence this needs, not five. If false, the estimator runs once and
        ``deterministic_across_two_calls`` is reported as ``None`` (not checked this section, not
        found false).
    """
    reference_full = stack[0]
    other_full = stack[1:]
    other_angles = angles_deg[1:] - angles_deg[0]
    other_angles_list = list(other_angles)

    reference_grid = reference_full[::GRID_DOWNSAMPLE, ::GRID_DOWNSAMPLE]
    other_grid = _downsample(other_full, GRID_DOWNSAMPLE)
    grid_estimate = estimate_rotation_centre(
        reference_grid, other_grid, other_angles_list, search_radius=40.0
    )
    grid_offset_full = (
        grid_estimate.offset_xy[0] * GRID_DOWNSAMPLE,
        grid_estimate.offset_xy[1] * GRID_DOWNSAMPLE,
    )

    # SIFT+RANSAC runs at its own, lighter downsample (see SIFT_DOWNSAMPLE's own comment) — it is
    # not the same array the grid search scores, deliberately — and on an evenly-spaced subsample
    # of at most MAX_SIFT_FRAMES frames, for the cost reason documented on that constant.
    reference_sift = reference_full[::SIFT_DOWNSAMPLE, ::SIFT_DOWNSAMPLE]
    frame_indices = _evenly_spaced_indices(len(other_full), MAX_SIFT_FRAMES)
    other_sift = [other_full[i][::SIFT_DOWNSAMPLE, ::SIFT_DOWNSAMPLE] for i in frame_indices]
    sift_angles_list = [other_angles_list[i] for i in frame_indices]

    sift_first = estimate_rotation_centre_sift_ransac(reference_sift, other_sift, sift_angles_list)
    if check_determinism:
        sift_second = estimate_rotation_centre_sift_ransac(
            reference_sift, other_sift, sift_angles_list
        )
        sift_deterministic: bool | None = sift_first.offset_xy == sift_second.offset_xy and all(
            a == b for a, b in zip(sift_first.per_frame, sift_second.per_frame, strict=True)
        )
    else:
        sift_deterministic = None
    sift_offset_full = (
        None
        if sift_first.offset_xy is None
        else (
            sift_first.offset_xy[0] * SIFT_DOWNSAMPLE,
            sift_first.offset_xy[1] * SIFT_DOWNSAMPLE,
        )
    )

    angles_rad = np.deg2rad(angles_deg - angles_deg[0])

    naive_signature = _harmonic_for_offset(
        reference_full, other_full, other_angles, angles_rad, (0.0, 0.0)
    )
    grid_signature = _harmonic_for_offset(
        reference_full, other_full, other_angles, angles_rad, grid_offset_full
    )
    sift_signature = _harmonic_for_offset(
        reference_full, other_full, other_angles, angles_rad, sift_offset_full
    )

    return {
        "naive": naive_signature,
        "grid_search": {
            "offset_xy_full_res": grid_offset_full,
            "improves_on_naive": grid_estimate.improves_on_naive_derotation,
            **(grid_signature or {}),
        },
        "sift_ransac": {
            "offset_xy_full_res": sift_offset_full,
            "deterministic_across_two_calls": sift_deterministic,
            "frames_used": len(frame_indices),
            "frames_available": len(other_full),
            "usable_frame_count": sift_first.usable_frame_count,
            "frame_count": len(sift_first.per_frame),
            "per_frame_inlier_counts": [f.inlier_count for f in sift_first.per_frame],
            "per_frame_residual_rms": [f.residual_rms for f in sift_first.per_frame],
            "per_frame_fitted_vs_nominal_angle_deg": [
                (f.fitted_angle_deg, f.angle_deg) for f in sift_first.per_frame
            ],
            **({} if sift_signature is None else sift_signature),
            "harmonic_verdict_available": sift_signature is not None,
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
    parser.add_argument("--output", type=Path, default=Path("sift-ransac-comparison.json"))
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
        determinism_checked = False
        for split, stem in sections[: args.sections]:
            outcome = load_section(archive, names, split, stem, geometry_experiment.section_frames)
            if isinstance(outcome, str):
                print(f"{split}/{stem}: SKIPPED ({outcome})")
                results[f"{split}/{stem}"] = {"skipped": outcome}
                continue
            stack, angles_deg = outcome
            print(f"{split}/{stem}: {stack.shape[0]} frames, {stack.shape[1]}x{stack.shape[2]}")
            check_this_section = not determinism_checked
            comparison = compare_methods(stack, angles_deg, check_determinism=check_this_section)
            determinism_checked = True
            results[f"{split}/{stem}"] = comparison

            naive = comparison["naive"]
            grid = comparison["grid_search"]
            sift = comparison["sift_ransac"]
            print(
                f"  naive:      {naive['verdict']:8s} snr_2={naive['snr_2']:.2f} "
                f"snr_4={naive['snr_4']:.2f}"
            )
            print(
                f"  grid:       offset={grid['offset_xy_full_res']} "
                f"improves={grid['improves_on_naive']} "
                f"verdict={grid.get('verdict', 'n/a')}"
            )
            determinism_label = (
                "not checked this section"
                if sift["deterministic_across_two_calls"] is None
                else str(sift["deterministic_across_two_calls"])
            )
            print(
                f"  sift+ransac: offset={sift['offset_xy_full_res']} "
                f"frames={sift['frames_used']}/{sift['frames_available']} "
                f"deterministic={determinism_label} "
                f"usable={sift['usable_frame_count']}/{sift['frame_count']} "
                f"verdict={sift.get('verdict', 'n/a')}"
            )
            if sift["deterministic_across_two_calls"] is False:
                print(
                    "  ** WARNING: SIFT+RANSAC failed the determinism check on this section — "
                    "its offset above should NOT be trusted, same rule as the grid search. **"
                )
    finally:
        if archive_cm is not None:
            archive_cm.__exit__(None, None, None)

    args.output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {args.output}")


if __name__ == "__main__":
    main()
