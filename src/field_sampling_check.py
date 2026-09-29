"""How much evidence does each dashboard mode decide on, and does it agree with the section?

    python -m src.field_sampling_check

For every held-out S2 section: the payload-bearing particle count and the
advisor's recommendation from (a) the expert-annotated whole section, (b) the
model's whole section, (c) the old single centre field, and (d) the six
sampled fields now used live. The advisor includes the evidence-sufficiency
gate (fewer than MIN_PAYLOAD_PARTICLES payload particles -> no recommendation).

The six-field grid was fixed by a latency budget before this ran; this file
reports its outcome on the test set, it was not used to choose it.
"""
import hashlib
import json

import numpy as np
import torch
from PIL import Image

from . import advisor, modal
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.patches import labels_for, multi_field_predict, single_field_predict

Image.MAX_IMAGE_PIXELS = None
CKPT = config.ROOT / "checkpoints" / "lumenstone_s2_patches" / "best.pt"
CACHE = config.ROOT / "data" / "derived" / "preds_s2_patches"


def measure(labels, confidence):
    result = modal.analyse(np.asarray(labels).astype(np.int64), ls.CLASS_NAMES, refine=True)
    return {"payload_particles": result.n_payload_particles,
            "action": advisor.advise(result, confidence).action}


def main():
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()
    _, _, test_ids = ls.split_ids()
    rows = []
    for stem in sorted(test_ids):
        cached = np.load(CACHE / f"{stem}.npz")
        image = Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg").convert("RGB")
        with torch.no_grad():
            single, single_conf, _ = single_field_predict(model, image, dev)
            multi, multi_conf, _, _ = multi_field_predict(model, image, dev)
        row = {
            "section": stem,
            "expert_whole": measure(labels_for(stem, "test"), 1.0),
            "model_whole": measure(cached["mask"], float(cached["confidence"])),
            "single_field": measure(single, single_conf),
            "six_fields": measure(multi, multi_conf),
        }
        rows.append(row)
        print(stem, {k: (v["payload_particles"], v["action"][:22]) for k, v in row.items() if k != "section"})

    def agree(mode):
        return sum(r[mode]["action"] == r["model_whole"]["action"] for r in rows)

    def refused(mode):
        return sum(r[mode]["action"].startswith("No recommendation - too few") for r in rows)

    summary = {
        "checkpoint_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
        "eval_set": sorted(test_ids),
        "min_payload_particles": advisor.MIN_PAYLOAD_PARTICLES,
        "agrees_with_model_whole_section": {"single_field": agree("single_field"), "six_fields": agree("six_fields")},
        "refused_too_few_particles": {m: refused(m) for m in ("expert_whole", "model_whole", "single_field", "six_fields")},
        "rows": rows,
    }
    out = config.REPORT_DIR / "field_sampling_s2.json"
    with open(out, "w") as handle:
        json.dump(summary, handle, indent=2)
    print("agrees with whole section:", summary["agrees_with_model_whole_section"])
    print("refused, too few payload particles:", summary["refused_too_few_particles"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
