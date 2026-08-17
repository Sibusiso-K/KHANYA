"""Score our model under the published LumenStone protocol, and compare.

    python -m src.benchmark                     # S2 (default subset)
    KHANYA_SUBSET=S1 python -m src.benchmark    # S1, directly comparable

Uses the CACHED predictions in data/derived/, so this is scoring only - no
inference. Run `python -m src.decision_gap --model patches` first if a cache is
missing.

Why this file exists. Our 0.5725 was being informally set against the published
0.88, and that comparison was invalid twice over: the published figures are
reported on S1 or on S1+S2 jointly rather than S2 alone, and petroscope evaluate
under a protocol we were not matching. Two protocol details matter:

  1. DATASET-WIDE accumulation. Metrics come from one confusion matrix summed
     over the whole test set, not a mean of per-image scores. We already did
     this, so no change - but it is worth confirming rather than assuming.

  2. VOID BORDERS. petroscope publish two IoU columns, plain and "void
     borders", the latter excluding pixels near class boundaries because a
     hand-drawn grain boundary is uncertain to within a few pixels. We were
     reporting only the stricter number and comparing it against their table
     without checking which column we were reading.

Published reference, ResUnet on LumenStone S1v1, from petroscope's readme.
"""
import argparse
import json

import numpy as np
import torch
from PIL import Image

from .segmentation import config, lumenstone as ls, metrics

Image.MAX_IMAGE_PIXELS = None

# petroscope readme, "Achieved metrics for LumenStone S1v1", ResUnet, 7 classes.
# Their labels map onto our class names as noted.
PUBLISHED_S1 = {
    "background": (0.8326, 0.8505),    # BG
    "bornite": (0.8868, 0.8955),       # Brt
    "chalcopyrite": (0.9191, 0.9363),  # Ccp
    "galena": (0.7464, 0.7630),        # Gl
    "pyrite": (0.9628, 0.9732),        # Py/Mrc - ours is pyrite only
    "sphalerite": (0.7534, 0.7653),    # Sph
    "tennantite": (0.7601, 0.7706),    # Tnt/Ttr
}
PUBLISHED_S1_MEAN = (0.8373, 0.8506)

# PSPNet + ResNet18 on S1+S2 jointly, mean IoU 0.88 / PA 0.96 (Korshunov et al.,
# Mining Science and Technology). Reported across both subsets, so it is not
# directly comparable to a single-subset number and is recorded for context only.
PUBLISHED_JOINT_MEAN_IOU = 0.88

BORDER_WIDTH = 5  # petroscope's default border voiding is a small odd element;
                  # 5 px on a 3396x2547 section is well under one grain width.


def truth_labels(stem):
    array = np.array(Image.open(ls.DATA_DIR / "masks" / "test" / f"{stem}.png"))
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[array.astype(np.int64)]


def score(model_name="patches", border_width=BORDER_WIDTH):
    cache_dir = (config.ROOT / "data" / "derived"
                 / f"preds_{ls.SUBSET.lower()}_{model_name}")
    _, _, test_ids = ls.split_ids()

    plain = metrics.new_confusion(ls.NUM_CLASSES)
    voided = metrics.new_confusion(ls.NUM_CLASSES)
    missing = []

    for stem in sorted(test_ids):
        cached = cache_dir / f"{stem}.npz"
        if not cached.exists():
            missing.append(stem)
            continue
        predicted = torch.from_numpy(np.load(cached)["mask"].astype(np.int64))
        truth = truth_labels(stem).long()
        metrics.confusion_from_batch(predicted, truth, ls.NUM_CLASSES, plain)
        valid = metrics.void_border_mask(truth, border_width)
        metrics.confusion_from_batch(
            predicted, truth, ls.NUM_CLASSES, voided, valid=valid
        )

    if missing:
        raise FileNotFoundError(
            f"No cached predictions for {missing}. Run:\n"
            f"  KHANYA_SUBSET={ls.SUBSET} python -m src.decision_gap "
            f"--model {model_name}"
        )
    return metrics.summarise(plain), metrics.summarise(voided)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("resize", "patches"), default="patches")
    parser.add_argument("--border-width", type=int, default=BORDER_WIDTH)
    args = parser.parse_args()

    plain, voided = score(args.model, args.border_width)
    published = PUBLISHED_S1 if ls.SUBSET == "S1" else {}

    header = f"{'class':16s}{'ours':>9s}{'ours+void':>11s}"
    if published:
        header += f"{'published':>11s}{'pub+void':>10s}{'gap':>8s}"
    print(f"\nLumenStone {ls.SUBSET}, {args.model} model, "
          f"{len(ls.CLASS_NAMES)} classes, border_width={args.border_width}")
    print(header)
    print("-" * len(header))

    for i, name in enumerate(ls.CLASS_NAMES):
        ours, ours_void = plain["iou_per_class"][i], voided["iou_per_class"][i]
        row = f"{name:16s}{ours:9.4f}{ours_void:11.4f}"
        if name in published:
            ref, ref_void = published[name]
            row += f"{ref:11.4f}{ref_void:10.4f}{ours_void - ref_void:+8.4f}"
        print(row)

    print("-" * len(header))
    row = f"{'MEAN':16s}{plain['mean_iou']:9.4f}{voided['mean_iou']:11.4f}"
    if published:
        row += (f"{PUBLISHED_S1_MEAN[0]:11.4f}{PUBLISHED_S1_MEAN[1]:10.4f}"
                f"{voided['mean_iou'] - PUBLISHED_S1_MEAN[1]:+8.4f}")
    print(row)
    print(f"{'pixel accuracy':16s}{plain['pixel_accuracy']:9.4f}"
          f"{voided['pixel_accuracy']:11.4f}")
    print(f"\nvoid-border protocol lifts our mean IoU by "
          f"{voided['mean_iou'] - plain['mean_iou']:+.4f}")
    if not published:
        print(f"No per-class published reference for {ls.SUBSET}. The joint "
              f"S1+S2 PSPNet figure (mean IoU {PUBLISHED_JOINT_MEAN_IOU}) spans "
              "two subsets and is not directly comparable.")

    out = config.REPORT_DIR / f"benchmark_{ls.SUBSET.lower()}_{args.model}.json"
    with open(out, "w") as f:
        json.dump({
            "subset": ls.SUBSET,
            "model": args.model,
            "border_width": args.border_width,
            "class_names": ls.CLASS_NAMES,
            "ours": plain,
            "ours_void_borders": voided,
            "published_resunet_s1v1": published or None,
            "published_resunet_s1v1_mean": PUBLISHED_S1_MEAN if published else None,
        }, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
