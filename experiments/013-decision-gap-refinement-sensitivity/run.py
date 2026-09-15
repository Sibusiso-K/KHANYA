"""The sensitivity analysis `khanya/main`'s own 2026-09-15 audit asked for, and assigned to this
side of the seam: does topology refinement (`modal.refine_ore_mask`, `modal.watershed_particles`)
change *which* sections the decision-gap comparison flags, not just how many.

    uv run python experiments/013-decision-gap-refinement-sensitivity/run.py

**Everything this reads is already committed to `khanya/main`** — no data transfer, no cross-
branch code copy (ADR-0003 stays intact: this script reads three small JSON files with
``git show``, it does not import or execute anything from `main`). Reproducible by anyone with
the repo, from this branch alone.

**Why this exists.** `reports/REFINEMENT-AUDIT-2026-09-15.md` measured two things about the
topology repair and rejected both as explanations for the decision-gap finding (it is not mostly
compensating for the dead magnetite channel; it is not systematically biasing liberation
conservative). It stopped short of checking whether raw and refined predictions flag the *same*
sections, only that the aggregate flip rate happens to match (6/12 in both
``reports/decision_gap_patches.json`` and ``reports/decision_gap_patches_refined.json``). An
identical rate is not the same as identical sections — this checks that, with a proper cluster
bootstrap (honest n, per Rule 4) and a paired exact test (not the chi-squared approximation,
which is not trustworthy at this sample size) rather than eyeballing two numbers that happen to
match.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from reefprint.trust.bootstrap import cluster_bootstrap_ci, paired_exact_test  # noqa: E402

#: Predeclared, matching the plan's own spec — see bootstrap.py's module docstring.
N_RESAMPLES = 2000
SEED = 0


def _read_khanya_json(path: str) -> dict:
    """Read one file from `khanya/main` as it exists in this checkout's git history — never a
    live copy, never a cross-branch import. ``git show`` returns exactly the committed bytes.
    """
    result = subprocess.run(
        ["git", "show", f"khanya/main:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    metrics = _read_khanya_json("reports/lumenstone_s2_patches_test_metrics.json")
    raw_gap = _read_khanya_json("reports/decision_gap_patches.json")
    refined_gap = _read_khanya_json("reports/decision_gap_patches_refined.json")

    rng = np.random.default_rng(SEED)

    # --- 1. Bootstrap CI on mean IoU across sections (P5's "bootstrap intervals" ask) ---
    section_ious = [row["mean_iou"] for row in metrics["per_image"].values()]
    iou_ci = cluster_bootstrap_ci(section_ious, rng=rng, n_resamples=N_RESAMPLES)
    print(f"S2 mean IoU across {len(section_ious)} sections: {iou_ci.describe()}")
    print()

    # --- 2. Bootstrap CI on the decision-gap flip rate, raw and refined separately ---
    raw_flips = {row["id"]: bool(row["flipped"]) for row in raw_gap["rows"]}
    refined_flips = {row["id"]: bool(row["flipped"]) for row in refined_gap["rows"]}

    raw_rate_ci = cluster_bootstrap_ci(
        [1.0 if v else 0.0 for v in raw_flips.values()],
        rng=np.random.default_rng(SEED),
        n_resamples=N_RESAMPLES,
    )
    refined_rate_ci = cluster_bootstrap_ci(
        [1.0 if v else 0.0 for v in refined_flips.values()],
        rng=np.random.default_rng(SEED),
        n_resamples=N_RESAMPLES,
    )
    print(f"Flip rate, raw predictions:      {raw_rate_ci.describe()}")
    print(f"Flip rate, refined predictions:  {refined_rate_ci.describe()}")
    print()

    # --- 3. Do raw and refined flag the SAME sections, not just the same count? ---
    disagreement = paired_exact_test(raw_flips, refined_flips)
    print("Which sections flip — raw vs refined:")
    print(f"  flips in raw only:      {list(disagreement.only_in_a)}")
    print(f"  flips in refined only:  {list(disagreement.only_in_b)}")
    print(f"  {disagreement.describe()}")
    print()

    both_flip = sorted(set(raw_flips) & {k for k in raw_flips if raw_flips[k] and refined_flips[k]})
    print(f"Sections flipped under BOTH conditions ({len(both_flip)}): {both_flip}")

    report = {
        "s2_mean_iou_bootstrap": {
            "point_estimate": iou_ci.point_estimate,
            "ci_low": iou_ci.low,
            "ci_high": iou_ci.high,
            "n_sections": iou_ci.n_units,
            "n_resamples": iou_ci.n_resamples,
        },
        "flip_rate_raw_bootstrap": {
            "point_estimate": raw_rate_ci.point_estimate,
            "ci_low": raw_rate_ci.low,
            "ci_high": raw_rate_ci.high,
        },
        "flip_rate_refined_bootstrap": {
            "point_estimate": refined_rate_ci.point_estimate,
            "ci_low": refined_rate_ci.low,
            "ci_high": refined_rate_ci.high,
        },
        "raw_only_flips": list(disagreement.only_in_a),
        "refined_only_flips": list(disagreement.only_in_b),
        "both_flip": both_flip,
        "mcnemar_exact_p_value": disagreement.p_value,
        "n_discordant": disagreement.n_discordant,
    }
    output_path = Path(__file__).parent / "sensitivity-report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {output_path}")


if __name__ == "__main__":
    main()
