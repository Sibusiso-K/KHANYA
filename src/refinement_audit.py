"""What does the boundary-topology refinement actually do to the measurement?

    python -m src.refinement_audit                  # S2 patches, cached preds

Reads the CACHED predictions in data/derived/, so this costs seconds - no
inference, no retraining.

WHY THIS FILE EXISTS. `modal.refine_ore_mask` plus `watershed_particles` sit
underneath every number this project reports: the decision-gap result, the
conformal band, the dashboard's association index. The refinement was justified
on topology grounds - speckle invents particles, holes split them, touching
grains merge - and those justifications are sound in principle. Nobody had
measured what the repair does in practice, on this data, with this checkpoint.

Three questions, each answered by a number rather than an argument:

  1. COMPOSITION. Of the pixels hole-filling adds to the ore mask, what were
     they really? If most are genuine ore the repair is recovering signal. If
     most are genuine background it is absorbing resin and pore space into
     particles, which is a different operation from the one described.

  2. MAGNETITE SHARE. `modal.py`'s own comment motivates hole filling partly by
     the magnetite collapse ("every magnetite inclusion becomes a hole"). If
     that were the dominant effect, the repair would be compensating for a dead
     output channel rather than fixing topology, and the decision-gap
     comparison would be confounded by it.

  3. DIRECTION AND MAGNITUDE. Liberation is payload area over particle area, so
     enlarging particles should depress it. Does it? And by how much - is this
     a correction or a replacement?

The answers are not what either hypothesis predicted; see
`reports/refinement_audit.json` and the report that cites it.
"""
import json

import numpy as np
import torch
from PIL import Image

from . import modal
from .segmentation import config, lumenstone as ls

PAYLOAD_CLASSES = ("chalcopyrite", "pentlandite")


def _ground_truth(stem, subdir="test"):
    codes = np.array(
        Image.open(ls.S2_DIR / "masks" / subdir / f"{stem}.png"), dtype=np.uint8
    )
    if codes.ndim == 3:
        codes = codes[:, :, 0]
    return ls._LOOKUP[torch.from_numpy(codes).long()].numpy().astype(np.int64)


def audit(pred_dir="data/derived/preds_s2_patches"):
    _, _, test_ids = ls.split_ids()
    payload_idx = [
        i for i, name in enumerate(ls.CLASS_NAMES) if name in PAYLOAD_CLASSES
    ]

    added_composition = np.zeros(ls.NUM_CLASSES, dtype=np.int64)
    added_total = 0
    magnetite_total = 0
    per_section = []

    for stem in test_ids:
        pred = np.load(f"{pred_dir}/{stem}.npz")["mask"].astype(np.int64)
        truth = _ground_truth(stem)

        ore = pred != 0
        added = modal.refine_ore_mask(ore) & ~ore
        added_composition += np.bincount(truth[added], minlength=ls.NUM_CLASSES)
        added_total += int(added.sum())
        magnetite_total += int((truth == 2).sum())

        payload_mask = np.isin(pred, payload_idx)
        raw, raw_n = modal.liberation_index(pred, payload_mask, refine=False)
        refined, refined_n = modal.liberation_index(pred, payload_mask, refine=True)
        per_section.append(
            {
                "section": stem,
                "liberation_raw": raw,
                "liberation_refined": refined,
                "delta": None if raw is None or refined is None else refined - raw,
                "particles_raw": raw_n,
                "particles_refined": refined_n,
            }
        )

    deltas = [s["delta"] for s in per_section if s["delta"] is not None]
    magnetite_added = int(added_composition[2])

    return {
        "subset": "S2",
        "model": "patches (current shipping checkpoint)",
        "n_test_sections": len(test_ids),
        "pred_dir": pred_dir,
        "class_names": ls.CLASS_NAMES,
        "hole_filling": {
            "pixels_added_to_ore": added_total,
            "true_composition_of_added": added_composition.tolist(),
            "share_truly_background": added_composition[0] / max(added_total, 1),
            "share_truly_ore": added_composition[1:].sum() / max(added_total, 1),
            "share_truly_magnetite": magnetite_added / max(added_total, 1),
            "magnetite_recovered_of_all_magnetite": (
                magnetite_added / max(magnetite_total, 1)
            ),
        },
        "liberation": {
            "per_section": per_section,
            "mean_delta": float(np.mean(deltas)) if deltas else None,
            "n_measurable": len(deltas),
            "n_lowered": sum(1 for d in deltas if d < 0),
            "n_raised": sum(1 for d in deltas if d > 0),
            "n_unchanged": sum(1 for d in deltas if d == 0),
            "max_abs_delta": float(max(abs(d) for d in deltas)) if deltas else None,
        },
        "morphology_constants": {
            "SPECKLE_KERNEL": modal.SPECKLE_KERNEL,
            "SEED_MIN_DISTANCE": modal.SEED_MIN_DISTANCE,
            "PEAK_FOOTPRINT": modal.PEAK_FOOTPRINT,
            "LIBERATION_THRESHOLD": modal.LIBERATION_THRESHOLD,
            "MIN_PARTICLE_PIXELS": modal.MIN_PARTICLE_PIXELS,
        },
    }


def main():
    result = audit()
    out = config.REPORTS_DIR / "refinement_audit.json" if hasattr(
        config, "REPORTS_DIR"
    ) else "reports/refinement_audit.json"
    with open(out, "w") as handle:
        json.dump(result, handle, indent=2)

    filling = result["hole_filling"]
    lib = result["liberation"]
    print(f"pixels added to ore by hole filling : {filling['pixels_added_to_ore']:,}")
    print(f"  truly background                  : {filling['share_truly_background']:.1%}")
    print(f"  truly ore                         : {filling['share_truly_ore']:.1%}")
    print(f"  truly magnetite                   : {filling['share_truly_magnetite']:.1%}")
    print()
    print(f"liberation mean delta (refined-raw) : {lib['mean_delta']:+.4f}")
    print(f"  lowered / raised / unchanged      : "
          f"{lib['n_lowered']} / {lib['n_raised']} / {lib['n_unchanged']}")
    print(f"  largest single-section swing      : {lib['max_abs_delta']:.4f}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
