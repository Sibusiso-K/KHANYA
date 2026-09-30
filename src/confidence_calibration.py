"""Evidence for two pre-production fixes, on train and validation sections only.

    python -m src.confidence_calibration

1. A confidence floor (finding 3 of reports/PREPROD-TEST-2026-09-30.md): does
   the six-field pipeline's mean confidence separate its correct confident
   calls from its wrong ones?
2. The advisory band: is the +/-0.335 band, calibrated on whole sections, wide
   enough for the noisier six-field estimate of the association index?

The 12 held-out test sections are not used (Lethabo's PR #7 decision). The
model has seen the 31 training sections, so its behaviour there is optimistic;
the 6 validation sections are unseen but few. Both are reported separately.
The reference is the advisor on the expert-annotated whole section, the same
policy src.decision_gap and src.lighting_check_validation use.
"""
import hashlib
import json
import time

import numpy as np
import torch
from PIL import Image

from . import advisor, modal
from .decision_gap import classify
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import labels_for, multi_field_predict

Image.MAX_IMAGE_PIXELS = None
CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"


def analyse(labels, confidence):
    result = modal.analyse(np.asarray(labels).astype(np.int64), ls.CLASS_NAMES, refine=True)
    return result, advisor.advise(result, confidence)


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
            expert, reference = analyse(labels_for(stem, "train"), 1.0)
            start = time.perf_counter()
            with torch.no_grad():
                labels, conf, _, _ = multi_field_predict(model, image, dev)
            seconds = time.perf_counter() - start
            fields, advice = analyse(labels, conf)
            severity = "agrees" if advice.action == reference.action else classify(reference.action, advice.action)
            rows.append({
                "section": stem, "split": split,
                "confidence": round(float(conf), 4),
                "six_field_liberation": None if fields.liberation is None else round(float(fields.liberation), 4),
                "expert_liberation": None if expert.liberation is None else round(float(expert.liberation), 4),
                "payload_particles": fields.n_payload_particles,
                "action": advice.action, "reference": reference.action,
                "confident": not advice.action.startswith(advisor.ABSTAINING_PREFIXES),
                "severity": severity, "seconds": round(seconds, 2),
            })
            print(f"{split[:5]} {stem} conf {conf:.3f} | {advice.action[:26]:26s} | ref {reference.action[:22]:22s} | {severity} | {seconds:.1f}s", flush=True)

    out = config.REPORT_DIR / "confidence_calibration_trainval.json"
    out.write_text(json.dumps({
        "checkpoint_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
        "test_sections_used": 0,
        "torch_threads": torch.get_num_threads(),
        "rows": rows,
    }, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
