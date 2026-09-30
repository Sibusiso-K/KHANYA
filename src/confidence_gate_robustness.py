"""Does the confidence gate still protect when the lighting really drifts?

    python -m src.confidence_gate_robustness

src/confidence_calibration.py found that, on train and validation sections,
the advisor's existing 0.85 "verify manually" threshold separated the six-field
pipeline's unsafe confident calls from its correct ones. That threshold was set
long before this data existed; nothing here fits a new one.

This run answers two follow-up questions:
1. Train + validation, darkened by src.stability's fixed RGB offset: if the
   lighting drifts by that much, do unsafe confident calls get past the gate?
2. The 12 held-out test sections, as imaged and darkened: DESCRIPTIVE ONLY,
   run after the rule was fixed, to say what the demo will show. Not used to
   choose anything.
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
CONFIDENCE_FLOOR = 0.85  # the advisor's pre-existing "high" threshold (src/advisor.py)


def advise(labels, confidence):
    result = modal.analyse(np.asarray(labels).astype(np.int64), ls.CLASS_NAMES, refine=True)
    return advisor.advise(result, confidence)


def row(model, dev, stem, split, folder, darkened):
    image = Image.open(ls.DATA_DIR / "imgs" / folder / f"{stem}.jpg").convert("RGB")
    reference = advise(labels_for(stem, folder), 1.0).action
    if darkened:
        image = stability.reimaged(image)
    with torch.no_grad():
        labels, conf, _, _ = multi_field_predict(model, image, dev)
    action = advise(labels, conf).action
    confident = not action.startswith(advisor.ABSTAINING_PREFIXES)
    severity = "agrees" if action == reference else classify(reference, action)
    return {"section": stem, "split": split, "darkened": darkened,
            "confidence": round(float(conf), 4), "action": action, "reference": reference,
            "confident": confident, "severity": severity,
            "passes_gate": confident and conf >= CONFIDENCE_FLOOR}


def summarise(rows):
    confident = [r for r in rows if r["confident"]]
    return {
        "sections": len(rows),
        "confident": len(confident),
        "unsafe_confident": sum(r["severity"] == "unsafe" for r in confident),
        "unsafe_past_gate": sum(r["severity"] == "unsafe" and r["passes_gate"] for r in confident),
        "correct_confident": sum(r["severity"] == "agrees" for r in confident),
        "correct_past_gate": sum(r["severity"] == "agrees" and r["passes_gate"] for r in confident),
    }


def main():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    train_ids, val_ids, test_ids = ls.split_ids()
    darkened = []
    for split, stems in (("validation", val_ids), ("train", train_ids)):
        for stem in sorted(stems):
            darkened.append(row(model, dev, stem, split, "train", True))
            print("darkened", stem, darkened[-1]["confidence"], darkened[-1]["action"][:26], darkened[-1]["severity"], flush=True)
    test = []
    for stem in sorted(test_ids):
        for dark in (False, True):
            test.append(row(model, dev, stem, "test", "test", dark))
            print("test", stem, "dark" if dark else "as imaged", test[-1]["confidence"], test[-1]["action"][:26], test[-1]["severity"], flush=True)
    sha = hashlib.sha256(CKPT.read_bytes()).hexdigest()
    (config.REPORT_DIR / "confidence_gate_darkened_trainval.json").write_text(json.dumps({
        "checkpoint_sha256": sha, "confidence_floor": CONFIDENCE_FLOOR,
        "shift_rgb": stability.REIMAGING_SHIFT_RGB, "test_sections_used": 0,
        "validation": summarise([r for r in darkened if r["split"] == "validation"]),
        "train_seen_by_model": summarise([r for r in darkened if r["split"] == "train"]),
        "rows": darkened}, indent=2) + "\n")
    (config.REPORT_DIR / "confidence_gate_test_descriptive.json").write_text(json.dumps({
        "checkpoint_sha256": sha, "confidence_floor": CONFIDENCE_FLOOR,
        "note": "descriptive only: run after the rule was fixed on train/val; chose nothing",
        "as_imaged": summarise([r for r in test if not r["darkened"]]),
        "darkened": summarise([r for r in test if r["darkened"]]),
        "rows": test}, indent=2) + "\n")
    print("wrote reports/confidence_gate_darkened_trainval.json and reports/confidence_gate_test_descriptive.json")


if __name__ == "__main__":
    main()
