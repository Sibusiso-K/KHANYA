"""Per-section S2 accuracy, bootstrap intervals, and Live Field vs full-section advice.

    python -m src.s2_section_stats

Three questions the accuracy report needs answered from files, not from memory:

  1. The headline 0.5725 pools every test pixel into one confusion matrix. What
     does each of the 12 sections score on its own? (REEFPRINT reported 0.4671
     averaging per-section means on 15 September; not reproduced until now.)
  2. How uncertain is the headline with only 12 sections? Percentile bootstrap
     over sections (the independent unit is a section, not a pixel).
  3. How often does the dashboard's fast single 512 px field give a different
     recommendation from the whole section?

Full-section predictions come from the cache in data/derived/preds_s2_patches,
generated from the same checkpoint on 16 August. Live Field predictions are run
fresh, exactly as the dashboard does.
"""
import hashlib
import json

import numpy as np
import torch
from PIL import Image

from . import modal
from .advisor import advise
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import labels_for, single_field_predict

Image.MAX_IMAGE_PIXELS = None
CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"
CACHE = config.ROOT / "data" / "derived" / "preds_s2_patches"
RESAMPLES, SEED = 2000, 42


def confusion(pred, truth):
    n = ls.NUM_CLASSES
    return np.bincount(truth.ravel() * n + pred.ravel(), minlength=n * n).reshape(n, n)


def ious(c):
    tp = np.diag(c).astype(float)
    union = c.sum(0) + c.sum(1) - tp
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(union > 0, tp / union, np.nan)


def main():
    _, _, test_ids = ls.split_ids()
    stems = sorted(test_ids)
    per_conf, rows = {}, []

    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()

    for stem in stems:
        cached = np.load(CACHE / f"{stem}.npz")
        pred = cached["mask"].astype(np.int64)
        truth = labels_for(stem, "test").astype(np.int64)
        c = confusion(pred, truth)
        per_conf[stem] = c
        full_action = advise(modal.analyse(pred, ls.CLASS_NAMES, refine=True),
                             float(cached["confidence"])).action

        image = Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg").convert("RGB")
        with torch.no_grad():
            live, live_conf, _ = single_field_predict(model, image, dev)
        live_action = advise(modal.analyse(np.asarray(live).astype(np.int64), ls.CLASS_NAMES,
                                           refine=True), float(live_conf)).action
        section_iou = ious(c)
        rows.append({
            "section": stem,
            "mean_iou_present_classes": float(np.nanmean(section_iou)),
            "iou_per_class": [None if np.isnan(v) else float(v) for v in section_iou],
            "full_section_advice": full_action,
            "live_field_advice": live_action,
            "advice_agrees": full_action == live_action,
        })

    pooled = ious(sum(per_conf.values()))
    per_section = np.array([r["mean_iou_present_classes"] for r in rows])

    rng = np.random.default_rng(SEED)
    boot_pooled, boot_mean = [], []
    for _ in range(RESAMPLES):
        pick = rng.integers(0, len(stems), len(stems))
        boot_pooled.append(np.nanmean(ious(sum(per_conf[stems[i]] for i in pick))))
        boot_mean.append(per_section[pick].mean())
    ci = lambda xs: [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))]

    agree = sum(r["advice_agrees"] for r in rows)
    result = {
        "checkpoint_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
        "eval_set": stems,
        "class_names": ls.CLASS_NAMES,
        "pooled_mean_iou": float(np.nanmean(pooled)),
        "pooled_mean_iou_bootstrap_95": ci(boot_pooled),
        "per_section_mean_iou_mean": float(per_section.mean()),
        "per_section_mean_iou_bootstrap_95": ci(boot_mean),
        "per_section_convention": "each section's IoU averaged over classes present in its ground truth or prediction",
        "n_sections_below_pooled": int((per_section < np.nanmean(pooled)).sum()),
        "bootstrap": {"unit": "section", "resamples": RESAMPLES, "seed": SEED, "method": "percentile"},
        "live_vs_full_advice_agree": agree,
        "rows": rows,
    }
    out = config.REPORT_DIR / "s2_section_stats.json"
    with open(out, "w") as handle:
        json.dump(result, handle, indent=2)
    print(f"pooled mIoU {result['pooled_mean_iou']:.4f}  95% CI {result['pooled_mean_iou_bootstrap_95']}")
    print(f"per-section mean {result['per_section_mean_iou_mean']:.4f}  95% CI {result['per_section_mean_iou_bootstrap_95']}")
    print(f"sections below pooled: {result['n_sections_below_pooled']}/12")
    print(f"live field agrees with full section: {agree}/12")
    for r in rows:
        print(f"  {r['section']}  {r['mean_iou_present_classes']:.4f}  full={r['full_section_advice'][:28]:28s} live={r['live_field_advice'][:28]}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
