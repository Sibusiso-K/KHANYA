"""Patch-based sampling at native resolution.

The resize baseline (train_lumenstone.py) downsamples 3396x2547 to 512x688 and
scores magnetite at IoU 0.000. Two causes are tangled together there: magnetite
is 1.84% of pixels, and a 6.6x linear downsample destroys fine grains before the
model ever sees them. Patch sampling at native resolution attacks both at once,
and is what the petroscope authors say is necessary - their README is explicit
that loss weighting and class weighting do NOT resolve mineral class imbalance,
and that they use patch-based probability-map sampling instead.

Two ideas, kept separate:

  1. NATIVE RESOLUTION. Patches are cropped from the full-size image, never
     resized. A 512x512 patch shows real grain boundaries at sensor resolution.

  2. BALANCED CENTRES. Patch centres are drawn by first picking a class
     uniformly, then picking a pixel of that class. Magnetite therefore centres
     ~20% of patches against its 1.84% area share - roughly 11x oversampling -
     without touching the loss function.

Note what balanced centring does and does not claim: centring a patch on a
magnetite pixel guarantees the class is PRESENT in that patch, not that it
dominates it. The pixel-level imbalance inside a patch is untouched. The fix is
to exposure, not to prior.
"""
import os
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import functional as TF

from . import lumenstone as ls

Image.MAX_IMAGE_PIXELS = None

PATCH = 512
BATCH_SIZE = 2

# Budget is env-overridable so a longer run needs no code edit, and — more
# importantly — so the defaults stay exactly what produced the recorded S2
# results. Unset means reproduce the report.
#
# S1 needed this: seven classes were trained on the same 64x8 budget as S2's
# five, and came out at mean IoU 0.33 with two classes near zero against a
# published 0.84. That is an undertrained model, not a method result, and it
# left our headline topology claim untestable.
PATCHES_PER_EPOCH = int(os.environ.get("KHANYA_PATCHES_PER_EPOCH", 64))
VAL_PATCHES = int(os.environ.get("KHANYA_VAL_PATCHES", 32))
EPOCHS = int(os.environ.get("KHANYA_EPOCHS", 8))
LR = 2e-4  # lower than the resize baseline's 1e-3: minerals sat at IoU 0.0 for
           # several epochs there, which is the signature of too high an LR for
           # a 5-class fine-tune of a pretrained backbone.
SEED = 42

# Cap on stored coordinates per (image, class). Full coordinate lists for
# 8.6M-pixel masks would be gigabytes; a random subsample of this size is ample
# for choosing patch centres and keeps the index at tens of megabytes.
MAX_COORDS = 20000

CACHE = ls.DATA_DIR.parent / f"{ls.SUBSET.lower()}_class_index.npz"


def labels_for(stem: str, subdir: str) -> np.ndarray:
    array = np.array(Image.open(ls.DATA_DIR / "masks" / subdir / f"{stem}.png"))
    if array.ndim == 3:
        array = array[:, :, 0]
    return ls._LOOKUP[torch.from_numpy(array).long()].numpy()


def build_class_index(ids, subdir="train", cache: Path = CACHE):
    """{(stem, class_index): array of (y, x)} for every class present.

    Cached to disk - scanning 31 full-resolution masks takes a couple of
    minutes and is pure overhead on every re-run.
    """
    if cache.exists():
        stored = np.load(cache, allow_pickle=True)
        if set(stored["ids"].tolist()) == set(ids):
            # Keys round-trip through npz as strings; the class index must come
            # back as int or every (stem, class) lookup silently misses.
            index = {}
            for key in stored.files:
                if key in ("ids", "shapes"):
                    continue
                stem, class_index = key.rsplit("|", 1)
                index[(stem, int(class_index))] = stored[key]
            return index, stored["shapes"].item()

    index, shapes = {}, {}
    rng = np.random.default_rng(SEED)
    for stem in ids:
        labels = labels_for(stem, subdir)
        shapes[stem] = labels.shape
        for class_index in range(ls.NUM_CLASSES):
            coords = np.argwhere(labels == class_index)
            if not len(coords):
                continue
            if len(coords) > MAX_COORDS:
                coords = coords[rng.choice(len(coords), MAX_COORDS, replace=False)]
            index[(stem, class_index)] = coords.astype(np.int32)
        print(f"  indexed {stem}: "
              + " ".join(f"{ls.CLASS_NAMES[c][:4]}={len(index[(stem, c)])}"
                         for c in range(ls.NUM_CLASSES) if (stem, c) in index))

    np.savez_compressed(
        cache, ids=np.array(ids), shapes=np.array(shapes, dtype=object),
        **{f"{stem}|{c}": v for (stem, c), v in index.items()},
    )
    return index, shapes


class BalancedPatches(Dataset):
    """Fixed-length view over an infinite sampler.

    __len__ is PATCHES_PER_EPOCH rather than a count of real examples: with 31
    source images there is no natural epoch, so an "epoch" is defined as a fixed
    patch budget. Reported epoch numbers mean patches seen, not passes over data.
    """

    def __init__(self, ids, index, shapes, subdir="train", length=PATCHES_PER_EPOCH,
                 train=True, seed=SEED):
        self.ids = ids
        self.index = index
        self.shapes = shapes
        self.subdir = subdir
        self.length = length
        self.train = train
        self.seed = seed
        self.classes_present = sorted({c for _, c in index})
        self._cache = {}

    def __len__(self):
        return self.length

    def _image(self, stem):
        if stem not in self._cache:
            # One decoded 3396x2547 RGB image is ~26MB; 31 of them would be
            # 800MB, so the cache is deliberately small and FIFO-evicted.
            if len(self._cache) >= 4:
                self._cache.pop(next(iter(self._cache)))
            self._cache[stem] = (
                np.array(Image.open(
                    ls.DATA_DIR / "imgs" / self.subdir / f"{stem}.jpg"
                ).convert("RGB")),
                labels_for(stem, self.subdir),
            )
        return self._cache[stem]

    def __getitem__(self, i):
        # Deterministic for val (fixed patches every epoch, so val numbers are
        # comparable across epochs), random for train.
        rng = random.Random(None if self.train else self.seed + i)

        target = rng.choice(self.classes_present)
        candidates = [s for s in self.ids if (s, target) in self.index]
        stem = rng.choice(candidates)
        coords = self.index[(stem, target)]
        y, x = coords[rng.randrange(len(coords))]

        height, width = self.shapes[stem]
        half = PATCH // 2
        top = int(np.clip(y - half, 0, max(0, height - PATCH)))
        left = int(np.clip(x - half, 0, max(0, width - PATCH)))

        image, labels = self._image(stem)
        image_patch = image[top:top + PATCH, left:left + PATCH]
        label_patch = labels[top:top + PATCH, left:left + PATCH]

        if self.train:
            if rng.random() < 0.5:
                image_patch, label_patch = image_patch[:, ::-1], label_patch[:, ::-1]
            if rng.random() < 0.5:
                image_patch, label_patch = image_patch[::-1], label_patch[::-1]

        tensor = TF.normalize(
            TF.to_tensor(np.ascontiguousarray(image_patch)),
            (0.485, 0.456, 0.406), (0.229, 0.224, 0.225),
        )
        return tensor, torch.from_numpy(np.ascontiguousarray(label_patch)).long()


def build_loaders():
    train_ids, val_ids, _ = ls.split_ids()
    print("building class index (cached after first run)...")
    index, shapes = build_class_index(sorted(train_ids + val_ids))

    train_index = {k: v for k, v in index.items() if k[0] in set(train_ids)}
    val_index = {k: v for k, v in index.items() if k[0] in set(val_ids)}

    make = lambda ids, idx, length, train: DataLoader(
        BalancedPatches(ids, idx, shapes, "train", length, train),
        batch_size=BATCH_SIZE, shuffle=False, num_workers=0, drop_last=train,
    )
    return (make(train_ids, train_index, PATCHES_PER_EPOCH, True),
            make(val_ids, val_index, VAL_PATCHES, False))


@torch.no_grad()
def sliding_window_predict(model, image, dev, patch=PATCH, overlap=64):
    """Full native-resolution prediction by tiling, with overlapping windows
    accumulated as logits so tile seams do not become visible label boundaries.

    This is the honest evaluation path: the model sees the whole section at the
    resolution it was trained on, rather than a downsampled version of it.
    """
    array = np.array(image.convert("RGB"))
    height, width = array.shape[:2]
    stride = patch - overlap

    accumulated = torch.zeros(ls.NUM_CLASSES, height, width, dtype=torch.float32)
    counts = torch.zeros(1, height, width, dtype=torch.float32)

    tops = list(range(0, max(1, height - patch + 1), stride))
    lefts = list(range(0, max(1, width - patch + 1), stride))
    if tops[-1] != height - patch:
        tops.append(max(0, height - patch))
    if lefts[-1] != width - patch:
        lefts.append(max(0, width - patch))

    for top in tops:
        for left in lefts:
            tile = array[top:top + patch, left:left + patch]
            tensor = TF.normalize(
                TF.to_tensor(np.ascontiguousarray(tile)),
                (0.485, 0.456, 0.406), (0.229, 0.224, 0.225),
            ).unsqueeze(0).to(dev)
            logits = model(tensor)["out"][0].cpu()
            accumulated[:, top:top + tile.shape[0], left:left + tile.shape[1]] += logits
            counts[:, top:top + tile.shape[0], left:left + tile.shape[1]] += 1

    probabilities = (accumulated / counts.clamp(min=1)).softmax(0)
    return probabilities.argmax(0).numpy(), probabilities.max(0).values.mean().item()
