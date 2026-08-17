"""Does the model survive a different microscope, operator and exposure?

    python -m src.robustness                  # all perturbations, resize model
    python -m src.robustness --model patches  # slower, native resolution

Every image we train and test on came from one laboratory, one microscope
(Carl Zeiss AxioScope 40) and one camera (Canon Powershot G10), under one
illumination setup. Nothing in our headline numbers says whether the model
survives a different rig - which is the first question a Mintek metallurgist
would ask before putting this in another lab.

This applies controlled photometric perturbations to the held-out test sections
and re-measures IoU. Ground-truth masks are untouched: the mineralogy has not
changed, only the imaging, so any drop is pure fragility.

WHAT THIS DOES NOT TEST, and must not be claimed to. These are synthetic
perturbations of the same underlying images. They probe sensitivity to exposure,
white balance, focus and sensor noise. They do NOT reproduce a genuinely
different optical train, different objective, different immersion medium, or
different polished-section preparation. For that, LumenStone V1 exists - the same
samples imaged under varying real conditions, built by the dataset authors
specifically for colour-adaptation work. Real V1 evidence beats synthetic
evidence and should replace this if there is time.

Nor does any of this make the model work on hand specimens or phone photographs.
Liberation and modal mineralogy are properties of a section plane at grain scale;
they are not recoverable from an image that never resolved individual grains.
"""
import argparse
import json

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter

from .segmentation import config, lumenstone as ls, metrics
from .segmentation.model import build_model, device
from .segmentation.train_lumenstone import CKPT

Image.MAX_IMAGE_PIXELS = None


def exposure(image, factor):
    return ImageEnhance.Brightness(image).enhance(factor)


def contrast(image, factor):
    return ImageEnhance.Contrast(image).enhance(factor)


def white_balance(image, warm):
    """Shift colour temperature. This is the perturbation most likely to hurt:
    reflectance AND colour are the diagnostic signal in reflected light, which
    is the whole basis of the optical-over-SEM argument, so a model that leans
    on absolute colour should degrade here more than under blur or noise."""
    array = np.asarray(image).astype(np.float32)
    array[..., 0] *= warm            # red
    array[..., 2] *= (2.0 - warm)    # blue, opposite direction
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))


def blur(image, radius):
    return image.filter(ImageFilter.GaussianBlur(radius))


def noise(image, sigma, seed=0):
    rng = np.random.default_rng(seed)
    array = np.asarray(image).astype(np.float32)
    array += rng.normal(0, sigma, array.shape)
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))


def jpeg(image, quality):
    import io
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


# Chosen to bracket what a different laboratory plausibly produces, not to break
# the model for effect. +/-30% exposure is an operator setting a camera by eye;
# 0.85/1.15 white balance is a different bulb or colour-temperature setting;
# blur 1.5px is slightly soft focus; JPEG 40 is an over-compressed archive image.
PERTURBATIONS = {
    "baseline": lambda im: im,
    "underexposed -30%": lambda im: exposure(im, 0.70),
    "overexposed +30%": lambda im: exposure(im, 1.30),
    "low contrast": lambda im: contrast(im, 0.70),
    "warm white balance": lambda im: white_balance(im, 1.15),
    "cool white balance": lambda im: white_balance(im, 0.85),
    "soft focus 1.5px": lambda im: blur(im, 1.5),
    "sensor noise s=8": lambda im: noise(im, 8),
    "JPEG quality 40": lambda im: jpeg(im, 40),
}


def grey_world(image):
    """Grey-world colour constancy: rescale each channel so channel means match.

    The classic illumination-invariance baseline. It assumes the average of a
    scene is achromatic, which is a strong assumption here - a section that is
    genuinely mostly one coloured phase will be partially neutralised, and that
    is a real cost, not a free fix.

    Included because the robustness sweep showed white balance is by far the
    dominant failure mode (-0.39 mean IoU against -0.001 for sensor noise). The
    question this answers is whether a standard, cheap normalisation recovers
    that loss, or whether the model needs illumination calibration at capture
    time - which is what quantitative reflectance microscopy already requires.
    """
    array = np.asarray(image).astype(np.float32)
    means = array.reshape(-1, 3).mean(0)
    array *= means.mean() / np.clip(means, 1e-6, None)
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))


def truth_labels(stem, size=None):
    image = Image.open(ls.DATA_DIR / "masks" / "test" / f"{stem}.png")
    if size is not None:
        image = image.resize(size, Image.NEAREST)
    array = np.array(image)
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[array.astype(np.int64)].long()


@torch.no_grad()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("resize", "patches"), default="resize")
    parser.add_argument("--normalise", action="store_true",
                        help="apply grey-world colour constancy after the "
                             "perturbation, before inference")
    args = parser.parse_args()

    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()

    _, _, test_ids = ls.split_ids()
    height, width = ls.IMAGE_HW
    results = {}

    for name, perturb in PERTURBATIONS.items():
        confusion = metrics.new_confusion(ls.NUM_CLASSES)
        for stem in sorted(test_ids):
            image = Image.open(
                ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg"
            ).convert("RGB")
            shown = perturb(image)
            if args.normalise:
                shown = grey_world(shown)
            predicted = model(
                ls.preprocess(shown).to(dev)
            )["out"][0].argmax(0).cpu()
            # Ground truth resized to the network's working size, unperturbed -
            # the mineralogy did not change, only the photograph of it.
            metrics.confusion_from_batch(
                predicted, truth_labels(stem, (width, height)),
                ls.NUM_CLASSES, confusion,
            )
        summary = metrics.summarise(confusion)
        results[name] = summary
        drop = summary["mean_iou"] - results["baseline"]["mean_iou"]
        print(f"{name:22s} mIoU {summary['mean_iou']:.4f}  "
              f"PA {summary['pixel_accuracy']:.4f}  "
              f"{'' if name == 'baseline' else f'{drop:+.4f}'}")

    config.REPORT_DIR.mkdir(exist_ok=True)
    suffix = "_greyworld" if args.normalise else ""
    out = (config.REPORT_DIR
           / f"robustness_{ls.SUBSET.lower()}_{args.model}{suffix}.json")
    with open(out, "w") as f:
        json.dump({
            "subset": ls.SUBSET, "model": args.model,
            "grey_world_normalised": args.normalise,
            "class_names": ls.CLASS_NAMES,
            "results": {k: v for k, v in results.items()},
        }, f, indent=2)
    print(f"\nwrote {out}")

    baseline = results["baseline"]["mean_iou"]
    worst = min(results.items(), key=lambda kv: kv[1]["mean_iou"])
    print(f"worst case: {worst[0]} at mIoU {worst[1]['mean_iou']:.4f} "
          f"({worst[1]['mean_iou'] - baseline:+.4f} vs baseline)")


if __name__ == "__main__":
    main()
