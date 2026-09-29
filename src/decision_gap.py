"""What does segmentation error actually cost at the decision layer?

    python -m src.decision_gap

Per-class IoU says how wrong the mask is. It does not say whether being that
wrong changes what the plant is told to do. This runs the full advisor path
twice over the same held-out sections - once on ground-truth masks, once on
predicted masks - and reports where the recommendation flips.

That flip rate is the number worth defending: a model can lose IoU on a phase
that no threshold depends on and change no decision at all, or it can miss a
small payload grain and flip "grind finer" to "continue at setpoint", which is
the expensive direction.
"""
import json

import numpy as np
import torch
from PIL import Image

from . import advisor, modal
from .segmentation import config, lumenstone as ls
from .segmentation.model import build_model, device
from .segmentation.train_lumenstone import CKPT


def ground_truth_labels(stem, subdir="test", match_prediction_size=True):
    """Ground-truth mask as contiguous class indices.

    Downsampled to the network's working size by default, because the
    comparison in this module must be like for like. Ground truth is native
    3396x2547 and predictions are 512x688, so the same physical grain carries
    ~44x fewer pixels in a prediction; leaving them at different resolutions
    would make MIN_PARTICLE_PIXELS discard far more particles on the predicted
    side and manufacture recommendation flips that are an artefact of scale
    rather than of model error. NEAREST only - interpolating class indices
    would invent minerals that do not exist.
    """
    image = Image.open(ls.DATA_DIR / "masks" / subdir / f"{stem}.png")
    if match_prediction_size:
        height, width = ls.IMAGE_HW
        image = image.resize((width, height), Image.NEAREST)
    array = np.array(image)
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[torch.from_numpy(array).long()].numpy()


# A flip is not a single kind of error. Counting a hedge the same as a
# confident wrong instruction would understate the uncertainty band, whose
# entire purpose is to convert the former into the latter.
UNSAFE_ACTIONS = ("Continue at current setpoint",)
# Every abstention the advisor can issue, taken from the advisor itself so a new
# refusal cannot be scored as a confident error. Before 2026-09-30 this listed
# only Marginal and Flag, so "No recommendation" would have counted as wrong.
HEDGED_ACTIONS = advisor.ABSTAINING_PREFIXES


def classify(truth_action, predicted_action):
    """Severity of a disagreement, from the plant's point of view."""
    if any(predicted_action.startswith(a) for a in HEDGED_ACTIONS):
        return "flagged"        # hedged: costs a check, loses nothing
    if any(predicted_action.startswith(a) for a in UNSAFE_ACTIONS):
        return "unsafe"         # told to carry on while payload is locked
    if any(truth_action.startswith(a) for a in UNSAFE_ACTIONS):
        return "conservative"   # acts when it need not: energy, not metal
    return "unsafe" if truth_action.startswith("Grind") else "conservative"


@torch.no_grad()
def main(model_name="resize", refine=False):
    """model_name: 'resize' (train_lumenstone) or 'patches' (native sliding window).

    The patch model scores higher per-class, so the question this answers is
    whether better IoU actually buys better decisions - which is not guaranteed,
    since the thresholds sit on liberation and payload fraction rather than on
    IoU.
    """
    from .segmentation import patches as patch_module
    from .segmentation.train_patches import checkpoint_for

    dev = device()
    native = model_name == "patches"
    weights = checkpoint_for("ce") if native else CKPT
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(weights, map_location=dev))
    model.eval()
    print(f"model: {model_name}  weights: {weights}")

    # Predicted masks depend only on the model, never on the advisor policy or
    # the particle estimator, so they are cached. Inference over 12 native-
    # resolution sections costs over an hour; re-scoring a threshold change
    # against cached masks costs seconds. Threshold and policy work should not
    # be gated on GPU-less inference.
    cache_dir = config.ROOT / "data" / "derived" / f"preds_{ls.SUBSET.lower()}_{model_name}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    _, _, test_ids = ls.split_ids()
    rows, flips = [], 0

    for stem in sorted(test_ids):
        # The cache is keyed by model NAME, so a retrained checkpoint would
        # otherwise be silently scored against its predecessor's predictions -
        # a wrong-answer bug with no error message. Stamp the checkpoint's
        # modification time and invalidate when it moves.
        cached = cache_dir / f"{stem}.npz"
        stamp = weights.stat().st_mtime_ns
        if cached.exists() and int(np.load(cached).get("ckpt", -1)) == stamp:
            store = np.load(cached)
            predicted, confidence = store["mask"], float(store["confidence"])
        else:
            if cached.exists():
                print(f"  {stem}: checkpoint changed, re-predicting")
            image = Image.open(
                ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg"
            ).convert("RGB")
            # Everything is compared at NATIVE resolution, for both models.
            #
            # MIN_PARTICLE_PIXELS is a fixed pixel count, so it corresponds to a
            # different PHYSICAL grain size at each resolution. Comparing the
            # resize model at 512x688 and the patch model at native therefore
            # measures the models against two different references, and their
            # flip rates are not comparable - which is how a 33% and a 50%
            # appeared to be a regression when they were partly a change of
            # ruler. Native is also the operationally honest choice: a plant
            # receives a full-resolution mask whichever model produced it.
            if native:
                predicted, confidence = patch_module.sliding_window_predict(
                    model, image, dev
                )
            else:
                probabilities = model(
                    ls.preprocess(image).to(dev)
                )["out"][0].softmax(0)
                confidence = probabilities.max(0).values.mean().item()
                small = probabilities.argmax(0).cpu().numpy().astype(np.uint8)
                predicted = np.array(
                    Image.fromarray(small).resize(
                        (image.width, image.height), Image.NEAREST
                    )
                )
            np.savez_compressed(
                cached, mask=predicted.astype(np.uint8), confidence=confidence,
                ckpt=stamp,
            )

        truth = ground_truth_labels(stem, match_prediction_size=False)
        truth_result = modal.analyse(truth, ls.CLASS_NAMES, refine=refine)
        predicted_result = modal.analyse(predicted, ls.CLASS_NAMES, refine=refine)

        # margin=0 on ground truth: an annotation carries no estimator error,
        # and banding the reference would hide the disagreement being measured.
        truth_action = advisor.advise(truth_result, 1.0, liberation_margin=0.0).action
        predicted_action = advisor.advise(predicted_result, confidence).action
        flipped = truth_action != predicted_action
        flips += flipped
        severity = classify(truth_action, predicted_action) if flipped else "none"

        rows.append({
            "id": stem,
            "liberation_truth": truth_result.liberation,
            "liberation_predicted": predicted_result.liberation,
            "payload_truth": truth_result.role_fractions.get("payload", 0.0),
            "payload_predicted": predicted_result.role_fractions.get("payload", 0.0),
            "action_truth": truth_action,
            "action_predicted": predicted_action,
            "flipped": bool(flipped),
            "severity": severity,
        })

        def show(value):
            return "  n/a" if value is None else f"{value:5.0%}"

        print(
            f"{stem}  lib {show(truth_result.liberation)} -> "
            f"{show(predicted_result.liberation)}   "
            f"payload {truth_result.role_fractions.get('payload', 0.0):5.1%} -> "
            f"{predicted_result.role_fractions.get('payload', 0.0):5.1%}   "
            f"{'FLIP' if flipped else '   .'}  {predicted_action}"
        )

    summary = {
        "model": model_name,
        "refine": refine,
        "n_sections": len(rows),
        "n_recommendation_flips": flips,
        "flip_rate": flips / len(rows),
        "severity_counts": {
            level: sum(1 for r in rows if r["severity"] == level)
            for level in ("unsafe", "conservative", "flagged")
        },
        "rows": rows,
    }
    counts = summary["severity_counts"]
    print(f"\n  unsafe  (confident wrong, metal at risk):    {counts['unsafe']}")
    print(f"  conservative (wasted energy, no metal lost): {counts['conservative']}")
    print(f"  flagged (hedged to manual review):           {counts['flagged']}")
    print(f"\n{flips}/{len(rows)} recommendations flipped "
          f"({summary['flip_rate']:.0%}) when running on predicted masks.")

    config.REPORT_DIR.mkdir(exist_ok=True)
    suffix = f"_{ls.SUBSET.lower()}" if ls.SUBSET != "S2" else ""
    suffix += "" if model_name == "resize" else f"_{model_name}"
    suffix += "_refined" if refine else ""
    out = config.REPORT_DIR / f"decision_gap{suffix}.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("resize", "patches"), default="resize")
    parser.add_argument("--refine", action="store_true", help="watershed + hole-fill particle refinement")
    args = parser.parse_args()
    main(args.model, args.refine)
