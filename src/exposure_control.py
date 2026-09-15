"""In-domain control for the V1 illumination finding.

    python -m src.exposure_control

src/v1_consistency.py measures how far the pipeline's output moves between two
real imagings of the same polished section (LumenStone V1). Its weakness is that
V1 ships no masks, so "the answer moved" cannot be separated from "the model was
never in domain here" by that experiment alone.

This control removes that ambiguity. It takes the twelve LABELLED, in-domain S2
held-out test sections, applies a synthetic exposure shift of -35 RGB - the
magnitude actually measured between V1's registered image pairs, not a round
number - and asks the same question: does the recommendation change?

Nothing here is cross-dataset. Same subset, same checkpoint, same test sections
the headline numbers are computed on. The only thing that changed is the
brightness.
"""
import json

import numpy as np
import torch
from PIL import Image

from . import advisor, modal
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import single_field_predict

Image.MAX_IMAGE_PIXELS = None

EXPOSURE_SHIFT = -35.0   # RGB points; measured between V1 base and b pairs
CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"


def pairwise_iou(a, b):
    out = []
    for k in range(ls.NUM_CLASSES):
        pa, pb = a == k, b == k
        union = np.logical_or(pa, pb).sum()
        if union:
            out.append(float(np.logical_and(pa, pb).sum()) / float(union))
    return float(np.mean(out)) if out else None


def main():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()

    _, _, test_ids = ls.split_ids()
    rows, changed = [], 0
    for stem in test_ids:
        image = Image.open(ls.S2_DIR / "imgs" / "test" / f"{stem}.jpg").convert("RGB")
        shifted = Image.fromarray(
            np.clip(np.asarray(image, np.float32) + EXPOSURE_SHIFT, 0, 255).astype(np.uint8)
        )
        got = {}
        for tag, img in (("orig", image), ("shifted", shifted)):
            mask, confidence, _ = single_field_predict(model, img, dev)
            mask = np.asarray(mask)
            result = modal.analyse(mask, ls.CLASS_NAMES, roles=modal.S2_ROLES, refine=True)
            got[tag] = (mask, advisor.advise(result, float(np.mean(confidence))).action,
                        result.liberation)
        flipped = got["orig"][1] != got["shifted"][1]
        changed += flipped
        rows.append({
            "section": stem,
            "mask_iou": pairwise_iou(got["orig"][0], got["shifted"][0]),
            "action_orig": got["orig"][1],
            "action_shifted": got["shifted"][1],
            "action_changed": bool(flipped),
            "liberation_orig": got["orig"][2],
            "liberation_shifted": got["shifted"][2],
        })
        show = lambda v: "n/a" if v is None else f"{v:.3f}"
        print(f"{stem}  IoU {rows[-1]['mask_iou']:.3f}  "
              f"lib {show(got['orig'][2])}->{show(got['shifted'][2])}  "
              f"{'ACTION CHANGED' if flipped else 'stable'}")

    ious = [r["mask_iou"] for r in rows if r["mask_iou"] is not None]
    summary = {
        "control": "S2 held-out test sections, synthetic exposure shift",
        "subset": ls.SUBSET,
        "checkpoint": str(CKPT),
        "exposure_shift_rgb": EXPOSURE_SHIFT,
        "field": "centre 512 crop",
        "n_sections": len(rows),
        "mean_mask_iou": float(np.mean(ious)),
        "n_action_changed": changed,
        "rows": rows,
    }
    out = config.ROOT / "reports" / "exposure_control_s2.json"
    with open(out, "w") as handle:
        json.dump(summary, handle, indent=2)
    print(f"\nmean mask IoU (same section, {EXPOSURE_SHIFT:+.0f} RGB): "
          f"{summary['mean_mask_iou']:.4f}")
    print(f"recommendation changed: {changed}/{len(rows)} sections")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
