"""Kaggle entry point for experiment 011. Locates the two mounted datasets, wires
``reefprint-code``'s ``src/`` onto ``sys.path``, and calls ``run.py``'s ``main()`` against the
extracted LumenStone S3 v2 dataset directory.

Not committed as part of the reefprint-code dataset itself (it is the kernel's own code_file, per
``kernel-metadata.json``, uploaded directly by ``kaggle kernels push``) — same reason
``experiments/007-s3v2-registration/kernel_entry.py`` keeps its own Kaggle-specific mount-
discovery glue out of the reusable ``run.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _find(base: Path, fragment: str) -> Path:
    for candidate in base.rglob("*"):
        if candidate.is_dir() and fragment in str(candidate).replace("\\", "/"):
            return candidate
    raise SystemExit(f"could not find a directory matching {fragment!r} under {base}")


def main() -> None:
    kaggle_input = Path("/kaggle/input")
    code_root = _find(kaggle_input, "reefprint-code")
    archive_root = _find(kaggle_input, "lumenstone-s3-v2-reefprint")

    # reefprint-code's dataset version uploaded `src.zip` and `experiments.zip` as separate
    # archives (kaggle datasets version -r zip); Kaggle auto-extracts each into its own
    # same-named directory under the dataset root.
    src_dir = _find(code_root, "/src") if not (code_root / "src").exists() else code_root / "src"
    experiments_dir = (
        _find(code_root, "/experiments")
        if not (code_root / "experiments").exists()
        else code_root / "experiments"
    )

    sys.path.insert(0, str(src_dir))

    run_path = experiments_dir / "011-sift-ransac-registration" / "run.py"
    spec = importlib.util.spec_from_file_location("sift_ransac_registration_experiment", run_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {run_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Emulate `run.py --archive-dir <archive_root> --sections 12 --output ...` without going
    # through argparse's sys.argv, since a Kaggle script kernel's own argv is not this script's
    # to control. --sections 12 matches experiment 007's own kernel_entry.py: several of the
    # first 12 sections are skipped (0 rotation frames, a mismatched frame), and it takes
    # attempting 12 to net the same 5 measurable sections (S3_test_01/02/03/07/12) that
    # 007-010 all report on, which is what makes this experiment's results comparable to theirs.
    sys.argv = [
        "run.py",
        "--archive-dir",
        str(archive_root),
        "--sections",
        "12",
        "--output",
        "/kaggle/working/sift-ransac-comparison.json",
    ]
    module.main()


if __name__ == "__main__":
    main()
