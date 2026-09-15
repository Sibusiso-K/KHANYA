"""Does the advice change when only the microscope changes?

    python -m src.v1_consistency              # centre field, fast
    python -m src.v1_consistency --full       # full section, sliding window

LumenStone V1 is ten polished sections, each imaged more than once under
different real conditions. The mineralogy is identical across imagings by
construction - only the optics changed - so any movement in our output is
imaging fragility measured on real optical variation, not on
`ImageEnhance.Brightness`.

WHY THIS EXISTS RATHER THAN A V1 RUN OF src/robustness.py. `robustness.py`'s
docstring says real V1 evidence should replace its synthetic perturbations. It
cannot, as written: `robustness.py` scores IoU against ground-truth masks and
**V1 ships no masks** - the dataset's own distribution table lists S1 and S2 as
"images + masks + visualizations" and V1 as "images (3 variations)". So this
measures self-consistency instead, which needs no ground truth: the same section
must give the same answer twice.

WHICH PAIRS ARE VALID, CHECKED RATHER THAN ASSUMED. V1 ships three files per
sample (`NNN`, `NNNa`, `NNNb`). They are not three imagings of one field:

  - `NNN` vs `NNNb`: 3396x2547 both, normalised cross-correlation 0.99 at zero
    shift on all ten samples. Pixel-registered. Valid for per-pixel comparison.
  - `NNNa`: 4272x2848, a different aspect ratio and a different camera. Its best
    correlation against the base image over a full scale-and-offset sweep is
    0.27, against 0.99 for the registered pair. It does not image the same
    field under any translation or scale hypothesis, so it is EXCLUDED.

This check exists because the project has already been burned once by assuming
registration: the S3 rotation series turned out to be unregistered, which
invalidated every per-pixel measurement taken on it. Ten valid pairs, not
fifteen, and the exclusion is reported rather than quietly dropped.

WHAT THIS DOES NOT SHOW. n = 10 sections from one laboratory. It is a fragility
probe, not a robustness guarantee, and V1 carries no labels, so a stable answer
here means "stable", not "correct" - the model could be consistently wrong.
"""
import argparse
import json

import numpy as np
import torch
from PIL import Image

from . import advisor, modal
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import single_field_predict, sliding_window_predict

Image.MAX_IMAGE_PIXELS = None

V1_DIR = config.ROOT / "data" / "raw" / "lumenstone" / "V1_v1" / "V1_v1"
SAMPLES = [f"{i:03d}" for i in range(1, 11)]
VARIANTS = ("", "b")          # "a" excluded, see module docstring

# V1 IS S1, NOT S2. The dataset page states it plainly: "V1: A specialized
# dataset featuring THE SAME SAMPLES AS FOR S1 imaged under varying
# conditions". S1 is Berezovskoe hydrothermal ore (sphalerite, pyrite, galena,
# bornite, tennantite, chalcopyrite); S2 is Norilsk (pyrrhotite, chalcopyrite,
# pentlandite, magnetite). A first run of this experiment used the S2
# checkpoint and produced a dramatic instability result that was pure
# out-of-domain artefact - the same cross-dataset case BACKUP-DEMO-SCRIPT.md
# already uses as its refusal beat. Run this under KHANYA_SUBSET=S1.
CKPT = config.ROOT / "checkpoints" / "lumenstone_s1_patches" / "best.pt"
ROLES = {"S1": modal.S1_ROLES, "S2": modal.S2_ROLES, "S3": modal.S3_ROLES}[ls.SUBSET]


def predict(model, path, dev, full):
    image = Image.open(path).convert("RGB")
    if full:
        mask, conf = sliding_window_predict(model, image, dev)
    else:
        # single_field_predict returns (labels, mean_confidence, cropped_image);
        # the crop is discarded here because base and b are pixel-registered, so
        # the centre crop is the same physical field in both.
        mask, conf, _ = single_field_predict(model, image, dev)
    return np.asarray(mask), float(np.mean(conf))


def measure(mask, confidence):
    result = modal.analyse(mask, ls.CLASS_NAMES, roles=ROLES, refine=True)
    rec = advisor.advise(result, confidence)
    return result, rec


def pairwise_iou(a, b):
    """Mean IoU treating one prediction as the other's reference."""
    ious = []
    for k in range(ls.NUM_CLASSES):
        pa, pb = a == k, b == k
        union = np.logical_or(pa, pb).sum()
        if union:
            ious.append(float(np.logical_and(pa, pb).sum()) / float(union))
    return float(np.mean(ious)) if ious else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="sliding window over the whole section (slow)")
    args = parser.parse_args()

    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()

    rows = []
    for stem in SAMPLES:
        out = {}
        for variant in VARIANTS:
            mask, conf = predict(model, V1_DIR / f"{stem}{variant}.jpg", dev, args.full)
            result, rec = measure(mask, conf)
            out[variant or "base"] = {
                "mask": mask,
                "confidence": conf,
                "liberation": result.liberation,
                "fractions": dict(result.phase_fractions),
                "ore_area_fraction": result.ore_area_fraction,
                "n_particles": result.n_particles,
                "action": rec.action,
                "verdict": advisor.verdict_state(rec.action)[0],
            }
        base, alt = out["base"], out["b"]
        row = {
            "sample": stem,
            "mask_iou": pairwise_iou(base["mask"], alt["mask"]),
            "liberation_base": base["liberation"],
            "liberation_b": alt["liberation"],
            "confidence_base": base["confidence"],
            "confidence_b": alt["confidence"],
            "action_base": base["action"],
            "action_b": alt["action"],
            "verdict_base": base["verdict"],
            "verdict_b": alt["verdict"],
            "action_changed": base["action"] != alt["action"],
            "verdict_changed": base["verdict"] != alt["verdict"],
            "max_phase_drift_pp": max(
                abs(base["fractions"].get(n, 0.0) - alt["fractions"].get(n, 0.0))
                for n in ls.CLASS_NAMES
            ) * 100.0,
        }
        rows.append(row)
        lib = lambda v: "n/a" if v is None else f"{v:.3f}"
        print(f"{stem}  IoU {row['mask_iou']:.3f}  lib {lib(base['liberation'])}->"
              f"{lib(alt['liberation'])}  drift {row['max_phase_drift_pp']:.2f}pp  "
              f"{'ACTION CHANGED' if row['action_changed'] else 'stable'}")

    changed = sum(r["action_changed"] for r in rows)
    verdict_changed = sum(r["verdict_changed"] for r in rows)
    ious = [r["mask_iou"] for r in rows if r["mask_iou"] is not None]
    drifts = [r["max_phase_drift_pp"] for r in rows]
    summary = {
        "n_samples": len(rows),
        "subset": ls.SUBSET,
        "checkpoint": str(CKPT),
        "variants_compared": ["base", "b"],
        "variant_a_excluded": "different camera and field; best correlation 0.27 vs 0.99 for the registered pair",
        "field": "full section" if args.full else "centre 512 crop",
        "mean_mask_iou": float(np.mean(ious)) if ious else None,
        "min_mask_iou": float(np.min(ious)) if ious else None,
        "mean_max_phase_drift_pp": float(np.mean(drifts)),
        "max_max_phase_drift_pp": float(np.max(drifts)),
        "n_action_changed": changed,
        "n_verdict_changed": verdict_changed,
        "rows": rows,
    }
    out = config.ROOT / "reports" / (
        "v1_consistency_full.json" if args.full else "v1_consistency.json")
    with open(out, "w") as handle:
        json.dump(summary, handle, indent=2)
    print(f"\nmean mask IoU between imagings : {summary['mean_mask_iou']:.4f}"
          f"  (min {summary['min_mask_iou']:.4f})")
    print(f"mean max phase drift           : {summary['mean_max_phase_drift_pp']:.2f} pp"
          f"  (max {summary['max_max_phase_drift_pp']:.2f})")
    print(f"recommendation changed         : {changed}/{len(rows)} sections")
    print(f"verdict state changed          : {verdict_changed}/{len(rows)} sections")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
