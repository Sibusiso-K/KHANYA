"""Does the lighting check catch errors, and what correct advice does it cost?

    python -m src.lighting_check_validation

Validated on the 31 training and 6 validation S2 sections ONLY. The 12 held-out
test sections are not used: they have already been reused throughout development,
and a new refusal rule must not be judged on them (Lethabo's PR #7 decision).
The model has seen the training sections, so its behaviour there is optimistic;
the 6 validation sections are unseen but few. Both are reported separately.

For each section, the live six-field pipeline runs twice, once as imaged and
once after src.stability's measured re-imaging shift, and the advice is compared
with the advisor run on the expert-annotated whole section (the same reference
policy src.decision_gap uses: consistency with expert labels, not plant truth).
"""
import hashlib
import json

import numpy as np
import torch
from PIL import Image

from . import advisor, modal, stability
from .decision_gap import classify
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import labels_for, multi_field_predict

Image.MAX_IMAGE_PIXELS = None
CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"


def advise(labels, confidence):
    result = modal.analyse(np.asarray(labels).astype(np.int64), ls.CLASS_NAMES, refine=True)
    return advisor.advise(result, confidence)


def main():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    train_ids, val_ids, _ = ls.split_ids()
    rows = []
    for split, stems in (("validation", val_ids), ("train", train_ids)):
        for stem in sorted(stems):
            image = Image.open(ls.DATA_DIR / "imgs" / "train" / f"{stem}.jpg").convert("RGB")
            reference = advise(labels_for(stem, "train"), 1.0).action
            with torch.no_grad():
                labels, conf, _, _ = multi_field_predict(model, image, dev)
                shifted, shifted_conf, _, _ = multi_field_predict(model, stability.reimaged(image), dev)
            original = advise(labels, conf)
            reimaged_action = advise(shifted, shifted_conf).action
            gated = stability.gate(original, reimaged_action)
            row = {
                "section": stem, "split": split, "reference": reference,
                "original": original.action, "reimaged": reimaged_action, "gated": gated.action,
                "held_by_check": gated.action == stability.UNSTABLE_ACTION,
                "severity_before": classify(reference, original.action) if original.action != reference else "agrees",
                "severity_after": classify(reference, gated.action) if gated.action != reference else "agrees",
            }
            rows.append(row)
            print(split[:5], stem, "|", original.action[:24], "->", reimaged_action[:24],
                  "| held" if row["held_by_check"] else "", "| ref", reference[:20])

    def tally(split):
        sub = [r for r in rows if r["split"] == split]
        confident = [r for r in sub if not stability.is_abstaining(r["original"])]
        wrong = [r for r in confident if r["severity_before"] in ("unsafe", "conservative")]
        right = [r for r in confident if r["severity_before"] == "agrees"]
        return {
            "sections": len(sub),
            "confident_before": len(confident),
            "held_by_check": sum(r["held_by_check"] for r in sub),
            "confident_errors_before": len(wrong),
            "confident_errors_caught": sum(r["held_by_check"] for r in wrong),
            "unsafe_before": sum(r["severity_before"] == "unsafe" for r in sub),
            "unsafe_after": sum(r["severity_after"] == "unsafe" for r in sub),
            "correct_confident_before": len(right),
            "correct_confident_lost": sum(r["held_by_check"] for r in right),
        }

    summary = {
        "checkpoint_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
        "shift_rgb": stability.REIMAGING_SHIFT_RGB,
        "test_sections_used": 0,
        "validation": tally("validation"),
        "train_seen_by_model": tally("train"),
        "rows": rows,
    }
    out = config.REPORT_DIR / "lighting_check_trainval.json"
    with open(out, "w") as handle:
        json.dump(summary, handle, indent=2)
    print("validation:", summary["validation"])
    print("train (seen by model):", summary["train_seen_by_model"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
