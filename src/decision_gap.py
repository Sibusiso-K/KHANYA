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
    image = Image.open(ls.S2_DIR / "masks" / subdir / f"{stem}.png")
    if match_prediction_size:
        height, width = ls.IMAGE_HW
        image = image.resize((width, height), Image.NEAREST)
    array = np.array(image)
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[torch.from_numpy(array).long()].numpy()


@torch.no_grad()
def main(model_name="resize"):
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

    _, _, test_ids = ls.split_ids()
    rows, flips = [], 0

    for stem in sorted(test_ids):
        image = Image.open(ls.S2_DIR / "imgs" / "test" / f"{stem}.jpg").convert("RGB")
        if native:
            predicted, confidence = patch_module.sliding_window_predict(
                model, image, dev
            )
        else:
            probabilities = model(ls.preprocess(image).to(dev))["out"][0].softmax(0)
            predicted = probabilities.argmax(0).cpu().numpy()
            confidence = probabilities.max(0).values.mean().item()

        # Ground truth is matched to whatever resolution the prediction is at,
        # so the minimum-particle-size filter treats both identically.
        truth = ground_truth_labels(stem, match_prediction_size=not native)
        truth_result = modal.analyse(truth, ls.CLASS_NAMES)
        predicted_result = modal.analyse(predicted, ls.CLASS_NAMES)

        truth_action = advisor.advise(truth_result, 1.0).action
        predicted_action = advisor.advise(predicted_result, confidence).action
        flipped = truth_action != predicted_action
        flips += flipped

        rows.append({
            "id": stem,
            "liberation_truth": truth_result.liberation,
            "liberation_predicted": predicted_result.liberation,
            "payload_truth": truth_result.role_fractions.get("payload", 0.0),
            "payload_predicted": predicted_result.role_fractions.get("payload", 0.0),
            "action_truth": truth_action,
            "action_predicted": predicted_action,
            "flipped": bool(flipped),
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
        "n_sections": len(rows),
        "n_recommendation_flips": flips,
        "flip_rate": flips / len(rows),
        "rows": rows,
    }
    print(f"\n{flips}/{len(rows)} recommendations flipped "
          f"({summary['flip_rate']:.0%}) when running on predicted masks.")

    config.REPORT_DIR.mkdir(exist_ok=True)
    suffix = "" if model_name == "resize" else f"_{model_name}"
    out = config.REPORT_DIR / f"decision_gap{suffix}.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("resize", "patches"), default="resize")
    main(parser.parse_args().model)
