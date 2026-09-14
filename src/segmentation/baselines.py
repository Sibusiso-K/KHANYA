"""Trivial baselines for the accuracy report, per the 2026-09-12 review's
template: "Report both trivial baselines beside every metric; uplift against
the stronger." These exist to be beaten, not to compete - a real model that
cannot clear a majority-class or colour-only baseline by a wide margin has
not learned the phases, it has learned the class priors or the palette.

    python -m src.segmentation.baselines

Two baselines, both statistical, neither a mineralogical judgement (Rule 6):

- majority-class: predict the single most common training pixel class
  everywhere. Tests whether the real model beats "always guess background."
- colour-only: nearest-class-mean-RGB per pixel. Tests the review's own
  "colorimeter" concern directly - if this baseline scores close to the real
  model, the model may be discriminating phases by brightness/hue alone
  rather than texture or shape.

A metadata-only baseline (per the review's template) is not included:
LumenStone ships no locality/specimen/acquisition metadata beyond the image
itself (confirmed by inspection - see DATA-SOURCES.md), so there is nothing
for such a baseline to condition on that the majority-class baseline does
not already cover. Reported as "not applicable" rather than silently
omitted - see the written-out note in main()'s output.
"""
import json

import numpy as np
import torch
from PIL import Image

from . import config, lumenstone as ls, metrics, patches

#: Cap on train pixels sampled per class for the colour centroid - tractable
#: on a CPU laptop, not a domain-tuned figure. Native images are ~8.6M
#: pixels each; this keeps the whole pass to a few minutes.
MAX_PIXELS_PER_CLASS = 200_000
RNG_SEED = 0
#: Pixels classified per chunk during nearest-centroid prediction, to bound
#: peak memory on a full native-resolution image (~8.6M pixels).
CHUNK = 500_000


def majority_class_index(train_ids):
    shares = ls.class_pixel_shares(train_ids, subdir="train")
    return int(np.argmax(shares))


def majority_class_confusion(test_ids, majority_index):
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
    for stem in test_ids:
        truth = patches.labels_for(stem, "test")
        pred = np.full_like(truth, majority_index)
        metrics.confusion_from_batch(
            torch.from_numpy(pred), torch.from_numpy(truth), ls.NUM_CLASSES, confusion,
        )
    return confusion


def class_colour_centroids(train_ids, rng):
    """Mean RGB per class, from a bounded random subsample of labelled train
    pixels. Returns (centroids[NUM_CLASSES, 3], pixel_counts[NUM_CLASSES])."""
    per_image_cap = max(1, MAX_PIXELS_PER_CLASS // max(1, len(train_ids)))
    sums = np.zeros((ls.NUM_CLASSES, 3), dtype=np.float64)
    counts = np.zeros(ls.NUM_CLASSES, dtype=np.int64)
    for stem in train_ids:
        image = np.array(Image.open(ls.DATA_DIR / "imgs" / "train" / f"{stem}.jpg"))
        truth = patches.labels_for(stem, "train")
        for c in range(ls.NUM_CLASSES):
            pixels = image[truth == c]
            if pixels.shape[0] == 0:
                continue
            if pixels.shape[0] > per_image_cap:
                idx = rng.choice(pixels.shape[0], per_image_cap, replace=False)
                pixels = pixels[idx]
            sums[c] += pixels.sum(axis=0)
            counts[c] += pixels.shape[0]
    centroids = sums / np.maximum(counts, 1)[:, None]
    return centroids, counts


def colour_only_predict(image, centroids):
    """Nearest-class-mean-RGB label for every pixel, chunked to bound memory."""
    flat = image.reshape(-1, 3).astype(np.float64)
    out = np.empty(flat.shape[0], dtype=np.int64)
    for start in range(0, flat.shape[0], CHUNK):
        chunk = flat[start:start + CHUNK]
        dists = ((chunk[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        out[start:start + CHUNK] = dists.argmin(axis=1)
    return out.reshape(image.shape[:2])


def colour_only_confusion(test_ids, centroids):
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
    for stem in test_ids:
        image = np.array(Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg"))
        truth = patches.labels_for(stem, "test")
        pred = colour_only_predict(image, centroids)
        metrics.confusion_from_batch(
            torch.from_numpy(pred), torch.from_numpy(truth), ls.NUM_CLASSES, confusion,
        )
    return confusion


def main():
    train_ids, _, test_ids = ls.split_ids()
    train_ids, test_ids = sorted(train_ids), sorted(test_ids)
    rng = np.random.default_rng(RNG_SEED)

    majority_index = majority_class_index(train_ids)
    print(f"majority class: {ls.CLASS_NAMES[majority_index]}")
    majority_summary = metrics.summarise(majority_class_confusion(test_ids, majority_index))
    majority_summary["class_names"] = ls.CLASS_NAMES
    majority_summary["baseline"] = "majority_class"
    majority_summary["majority_class"] = ls.CLASS_NAMES[majority_index]
    print(f"  mean IoU {majority_summary['mean_iou']:.4f}   "
          f"pixel accuracy {majority_summary['pixel_accuracy']:.4f}")

    print("computing colour centroids from train pixels (subsampled)...")
    centroids, counts = class_colour_centroids(train_ids, rng)
    for name, centroid, count in zip(ls.CLASS_NAMES, centroids, counts):
        print(f"  {name:14s} mean RGB {centroid.round(1).tolist()}  (n={count})")
    print("scoring colour-only baseline on the test set...")
    colour_summary = metrics.summarise(colour_only_confusion(test_ids, centroids))
    colour_summary["class_names"] = ls.CLASS_NAMES
    colour_summary["baseline"] = "colour_only_nearest_centroid"
    colour_summary["centroid_rgb_per_class"] = centroids.tolist()
    colour_summary["centroid_pixel_counts"] = counts.tolist()
    print(f"  mean IoU {colour_summary['mean_iou']:.4f}   "
          f"pixel accuracy {colour_summary['pixel_accuracy']:.4f}")

    payload = {
        "subset": ls.SUBSET,
        "n_train_images": len(train_ids),
        "n_test_images": len(test_ids),
        "majority_class_baseline": majority_summary,
        "colour_only_baseline": colour_summary,
        "metadata_only_baseline": (
            "not applicable - LumenStone ships no locality/specimen/"
            "acquisition metadata beyond the image itself (confirmed by "
            "inspection, DATA-SOURCES.md); nothing distinguishes it from "
            "the majority-class baseline above"
        ),
    }
    out = config.REPORT_DIR / f"lumenstone_{ls.SUBSET.lower()}_trivial_baselines.json"
    config.REPORT_DIR.mkdir(exist_ok=True)
    with open(out, "w") as f:
        json.dump(metrics.json_safe(payload), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
