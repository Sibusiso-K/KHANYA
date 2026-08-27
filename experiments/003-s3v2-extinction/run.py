"""Leg (b)'s actual route on the real archive: per-mineral extinction depth, not Stokes.

    uv run python experiments/003-s3v2-extinction/run.py --archive path/to/S3_v2.zip \
        --codebook path/to/codebook.json --locality lumenstone-s3

N3 (see CONTEXT.md, docs/BUILDLOG.md session 16d) measured `NEITHER` three times, independently,
on the real S3 v2 archive, and the brightness-restricted re-run — the one check that could have
overturned it — moved 2nd-harmonic SNR closer to threshold but did not clear it. That licenses
routing leg (b) through the fourth-harmonic estimator (`reefprint.polarim.extinction`) instead of
the Stokes inversion, which `experiments/002-s3v2-geometry/run.py` already confirmed would be the
wrong tool here.

THE MEMORY CONSTRAINT THIS SCRIPT IS BUILT AROUND, AND WHY IT IS WORSE THAN IT LOOKS. A full
section is 3396x2547 across up to 72 frames. `experiments/002-s3v2-geometry/run.py` never holds
a full frame stack — it decodes one frame at a time and samples scattered pixel positions,
because that's all a harmonic-strength check needs. `measure_section_extinction` needs the
opposite: a full per-pixel extinction map, because "which mineral extincts at all" is a per-pixel
question over the mask, not a distribution question over a sample. This loader therefore *does*
hold one full section's frame stack in memory, one section at a time.

It builds that stack as float32 (~2.5 GB for a full 3396x2547x72 section) to keep the decode step
cheap, **but `RotationSeries.__post_init__` (`reefprint.acquire.series`) unconditionally casts to
float64 on construction** — found by the test suite, not assumed — so peak memory for a full
section is closer to ~5 GB once the series object exists, not the ~2.5 GB a float32 stack alone
would cost. That upcast is `RotationSeries`'s existing, deliberate contract (every other caller
relies on it), not a bug to route around here. State the real number rather than the one that
would be convenient: **a full-resolution section needs ~5 GB free**, and `--sections` should be
kept small on a memory-constrained machine. This is the only sanctioned place in the codebase
that holds a full frame stack at all; never generalise the pattern elsewhere without re-deriving
the bound for whatever memory is actually available there.

THE CODEBOOK IS NOT THIS SCRIPT'S TO INVENT. `LabelledSection` requires a code-to-mineral-name
mapping. KHANYA's `src/polarimetry.py` already imports one for S3 v2, from
`.segmentation.lumenstone.CODEBOOK`, and that mapping is a mineralogical judgement call (which
mask pixel value is which mineral) that Rule 6 reserves for a human, already exercised once on
the KHANYA side. This script never derives one from mask colours; it takes one as JSON
(``{"code": "mineral_name", ...}``) and refuses to run without it, loudly, rather than guessing.
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

from reefprint.acquire.series import RotationGeometry, RotationSeries
from reefprint.bridge.extinction import measure_section_extinction
from reefprint.bridge.section import LabelledSection, LabelProvenance

#: Loaded by path, matching the convention `tests/test_s3v2_reader.py` already uses for
#: importing a numbered, non-package experiment script.
_GEOMETRY_EXPERIMENT_PATH = Path(__file__).resolve().parents[1] / "002-s3v2-geometry" / "run.py"


def _load_geometry_experiment() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "s3v2_geometry_experiment", _GEOMETRY_EXPERIMENT_PATH
    )
    if spec is None or spec.loader is None:  # pragma: no cover - would mean the file vanished
        raise SystemExit(f"cannot load {_GEOMETRY_EXPERIMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_section_as_specimen_series(
    archive: zipfile.ZipFile,
    names: list[str],
    split: str,
    stem: str,
    section_frames_fn: Callable[[list[str], str, str], list[tuple[int, str]]],
    *,
    codebook: dict[int, str],
    locality: str,
    section_id: str | None = None,
) -> tuple[LabelledSection, RotationSeries] | str:
    """Decode one section's full rotation series and mask into bridge objects.

    Returns ``(section, series)``, or a ``str`` reason if the section cannot be used — never
    raises on a shape mismatch, matching `experiments/002-s3v2-geometry/run.py::read_section`'s
    convention that a malformed section is a fact to report, not a crash to hit mid-archive.

    Args:
        archive: An open zip file.
        names: ``archive.namelist()``, passed in rather than recomputed per section.
        split: ``"train"`` or ``"test"``.
        stem: The section's stem, e.g. ``"S3_test_01"``.
        section_frames_fn: ``experiments/002-s3v2-geometry/run.py``'s ``section_frames`` —
            injected rather than imported at module scope, since that module is loaded by path.
        codebook: Mineral code to name. Not derived here — see module docstring.
        locality: Passed straight to `LabelledSection`. This script does not know what a
            LumenStone section's real-world locality is; the caller must supply one (Rule 2:
            a section without a locality cannot be split on, so it cannot be defaulted here
            to something that looks plausible).
        section_id: Defaults to ``stem`` if not given.
    """
    frames_meta = section_frames_fn(names, split, stem)
    if len(frames_meta) < 3:
        return f"only {len(frames_meta)} rotation frames"

    with archive.open(f"S3_v2/masks/{split}/{stem}.png") as handle:
        mask = np.array(Image.open(io.BytesIO(handle.read())))
    labels = mask[:, :, 0] if mask.ndim == 3 else mask
    labels = labels.astype(np.int64)

    height, width = labels.shape
    n_angles = len(frames_meta)
    # float32: see module docstring for why this, not float64, is the sanctioned dtype here.
    stack = np.empty((n_angles, height, width), dtype=np.float32)
    for i, (_deg, name) in enumerate(frames_meta):
        with archive.open(name) as handle:
            frame = np.array(Image.open(io.BytesIO(handle.read())).convert("L"))
        if frame.shape != labels.shape:
            return (
                f"frame {name.rsplit('/', 1)[-1]} shape {frame.shape} != mask shape {labels.shape}"
            )
        stack[i] = frame.astype(np.float32)

    angles_rad = np.deg2rad(np.array([deg for deg, _ in frames_meta], dtype=np.float64))
    series = RotationSeries(
        frames=stack,
        angles_rad=angles_rad,
        source=f"LumenStone S3 v2 archive, {split}/{stem}",
        geometry=RotationGeometry.SPECIMEN,
    )
    section = LabelledSection(
        labels=labels,
        codebook=codebook,
        section_id=section_id or stem,
        locality=locality,
        provenance=LabelProvenance.GROUND_TRUTH,
    )
    return section, series


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--codebook",
        type=Path,
        required=True,
        help="JSON file mapping mask pixel code (string) to mineral name. Not guessed here.",
    )
    parser.add_argument("--locality", type=str, required=True)
    parser.add_argument("--sections", type=int, default=6)
    args = parser.parse_args()

    if not args.archive.exists():
        raise SystemExit(f"not found: {args.archive}")
    if not args.codebook.exists():
        raise SystemExit(
            f"not found: {args.codebook}. This script does not derive a codebook from mask "
            "colours — see the module docstring for why. Point --codebook at KHANYA's real "
            'S3 v2 mapping, or a JSON file shaped {"0": "background", "1": "pyrite", ...}.'
        )
    codebook = {int(k): v for k, v in json.loads(args.codebook.read_text()).items()}

    geometry_experiment = _load_geometry_experiment()

    with zipfile.ZipFile(args.archive) as archive:
        names = [n for n in archive.namelist() if not n.startswith("__MACOSX")]
        sections = geometry_experiment.list_sections(names)
        print(
            f"{len(sections)} sections in archive; measuring {min(args.sections, len(sections))}\n"
        )

        for split, stem in sections[: args.sections]:
            result = load_section_as_specimen_series(
                archive,
                names,
                split,
                stem,
                geometry_experiment.section_frames,
                codebook=codebook,
                locality=args.locality,
            )
            if isinstance(result, str):
                print(f"{stem:22s}  SKIPPED: {result}")
                continue

            section, series = result
            measurement = measure_section_extinction(section, series)
            if not measurement.was_measured:
                print(f"{stem:22s}  SKIPPED: {measurement.skipped}")
                continue

            print(f"{stem} — {measurement.n_pixels_measured} pixels measured:")
            for stat in measurement.per_mineral:
                print(
                    f"  {stat.mineral:16s} n={stat.n_pixels:>7d}  "
                    f"depth median={stat.extinction_depth_median:.2f} "
                    f"(p25={stat.extinction_depth_p25:.2f}, p75={stat.extinction_depth_p75:.2f})  "
                    f"crossing_ratio={stat.crossing_ratio_median:.3f}"
                )


if __name__ == "__main__":
    main()
