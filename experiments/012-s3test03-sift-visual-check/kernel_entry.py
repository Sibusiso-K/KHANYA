"""Kaggle entry point for experiment 012. See ``experiments/007-s3v2-registration/
kernel_entry.py`` for the mount-discovery pattern this mirrors.
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

    src_dir = _find(code_root, "/src") if not (code_root / "src").exists() else code_root / "src"
    experiments_dir = (
        _find(code_root, "/experiments")
        if not (code_root / "experiments").exists()
        else code_root / "experiments"
    )

    sys.path.insert(0, str(src_dir))

    run_path = experiments_dir / "012-s3test03-sift-visual-check" / "run.py"
    spec = importlib.util.spec_from_file_location("s3test03_sift_visual_check", run_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {run_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    sys.argv = [
        "run.py",
        "--archive-dir",
        str(archive_root),
        "--output-dir",
        "/kaggle/working/output",
    ]
    module.main()


if __name__ == "__main__":
    main()
