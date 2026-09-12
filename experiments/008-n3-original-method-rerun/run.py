"""Checks experiment 007's own open hypothesis: does N3's ORIGINAL method (zero registration,
scattered raw pixel samples) still return ``NEITHER`` on the exact 5 sections experiment 007
measured — or does it agree with 007's "naive" condition (SECOND on all 5), which would mean the
discrepancy is not a registration effect at all?

    uv run python experiments/008-n3-original-method-rerun/run.py --archive path/to/S3_v2.zip
    uv run python experiments/008-n3-original-method-rerun/run.py --archive-dir path/to/extracted

**Why this experiment exists, in one sentence.** Experiment 007's README states, honestly, that
its "naive" condition (rotate every frame about the *image centre* by its nominal angle) is not
the same starting point as N3's original method (`experiments/002-s3v2-geometry/run.py`'s
`read_section`, which samples scattered pixel *positions* directly from raw, un-rotated frames —
genuinely zero registration) — and that this session had a hypothesis for why the two disagree,
not a check. This is that check.

**This script changes nothing about N3's method.** It calls `experiments/002`'s own
`read_section`, `harmonic_signature` and `pool_signatures` unchanged, restricted to the same five
section stems experiment 007 measured (`S3_test_01/02/03/07/12`), so the comparison is apples to
apples: same sections, same archive, same estimator, only the registration step differs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The exact sections experiment 007 measured and reported a naive-vs-registered comparison for.
#: Restricting to these, rather than a fresh --sections count, is what makes this a like-for-like
#: check rather than a new, differently-scoped sample.
TARGET_SECTIONS = ("S3_test_01", "S3_test_02", "S3_test_03", "S3_test_07", "S3_test_12")

#: experiment 007's own recorded naive-condition numbers, reproduced here (not recomputed) so
#: this script's output shows the comparison inline rather than asking the reader to hold two
#: reports open side by side. Source: experiments/007-s3v2-registration/README.md, run 2026-09-13.
EXPERIMENT_007_NAIVE = {
    "S3_test_01": {"snr_2": 12.538461639005282, "snr_4": 4.442915548874999, "verdict": "SECOND"},
    "S3_test_02": {"snr_2": 11.181677594635119, "snr_4": 3.537614162660208, "verdict": "SECOND"},
    "S3_test_03": {"snr_2": 9.350294830486483, "snr_4": 2.7758807045080824, "verdict": "SECOND"},
    "S3_test_07": {"snr_2": 6.89138718492273, "snr_4": 2.094748514985484, "verdict": "SECOND"},
    "S3_test_12": {"snr_2": 7.106078013285029, "snr_4": 2.6822424424690956, "verdict": "SECOND"},
}


class _DirArchive:
    """Duck-types :class:`zipfile.ZipFile` against an already-extracted directory — Kaggle
    auto-extracts an uploaded zip dataset rather than keeping it as one archive (session 16f).
    Matches ``experiments/007-s3v2-registration/run.py``'s own shim.
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


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="defaults to experiment 002's own SAMPLES_PER_SECTION",
    )
    parser.add_argument("--seed", type=int, default=20260820)
    parser.add_argument("--output", type=Path, default=Path("n3-rerun-report.json"))
    args = parser.parse_args()

    geometry = _load_geometry_experiment()
    n_samples = args.samples if args.samples is not None else geometry.SAMPLES_PER_SECTION

    if args.archive is not None:
        archive_cm = zipfile.ZipFile(args.archive)
        archive = archive_cm.__enter__()
    elif args.archive_dir is not None:
        archive_cm = None
        archive = _DirArchive(args.archive_dir)
    else:
        raise SystemExit("pass --archive path/to/S3_v2.zip or --archive-dir path/to/extracted")

    results: dict[str, object] = {}
    try:
        names = [n for n in archive.namelist() if "__MACOSX" not in n]
        sections = geometry.list_sections(names)
        wanted = {("test", stem) for stem in TARGET_SECTIONS}
        targets = [pair for pair in sections if pair in wanted]
        print(f"{len(targets)} of {len(TARGET_SECTIONS)} target sections found in archive\n")

        rng = np.random.default_rng(args.seed)
        columns = (
            "section",
            "n3-orig snr2",
            "n3-orig snr4",
            "verdict",
            "exp007 naive snr2",
            "exp007 naive snr4",
            "agree?",
        )
        widths = (14, 14, 14, 10, 20, 20, 8)
        header = "".join(f"{c:>{w}s}" for c, w in zip(columns, widths, strict=True))
        print(header)
        print("-" * len(header))

        for split, stem in targets:
            data = geometry.read_section(archive, names, split, stem, rng, n_samples=n_samples)
            if "skipped" in data:
                print(f"{stem:>14s}  SKIPPED: {data['skipped']}")
                results[stem] = {"skipped": data["skipped"]}
                continue

            signature = geometry.harmonic_signature(data["intensities"], data["angles_rad"])
            exp007 = EXPERIMENT_007_NAIVE[stem]
            agrees = signature.verdict.name == exp007["verdict"]
            row = (
                stem,
                f"{signature.snr_2:.2f}",
                f"{signature.snr_4:.2f}",
                signature.verdict.name,
                f"{exp007['snr_2']:.2f}",
                f"{exp007['snr_4']:.2f}",
                "YES" if agrees else "NO",
            )
            print("".join(f"{c:>{w}s}" for c, w in zip(row, widths, strict=True)))
            results[stem] = {
                "n3_original_snr_2": signature.snr_2,
                "n3_original_snr_4": signature.snr_4,
                "n3_original_verdict": signature.verdict.name,
                "experiment_007_naive_snr_2": exp007["snr_2"],
                "experiment_007_naive_snr_4": exp007["snr_4"],
                "experiment_007_naive_verdict": exp007["verdict"],
                "agrees_with_experiment_007_naive": agrees,
            }
    finally:
        if archive_cm is not None:
            archive_cm.__exit__(None, None, None)

    n_agree = sum(
        1
        for v in results.values()
        if isinstance(v, dict) and v.get("agrees_with_experiment_007_naive")
    )
    n_measured = sum(
        1 for v in results.values() if isinstance(v, dict) and "n3_original_verdict" in v
    )
    print(
        f"\n{n_agree}/{n_measured} sections: N3's original method agrees with experiment 007's naive condition"
    )

    args.output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
