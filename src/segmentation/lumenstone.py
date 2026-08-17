"""LumenStone S2 — multi-class segmentation data.

S2 is the Norilsk Group layered-ultramafic assemblage: chalcopyrite, magnetite,
pyrrhotite, pentlandite against resin background. Five classes clears the
brief's >=3 phase floor with a real held-out test set, and the assemblage is the
BMS analogue for Bushveld reef ores (see DATA-SOURCES.md Section 1, including
where that analogue breaks).

Kept separate from data.py rather than folded into it: the FeM binary pipeline
produced the 0.872 mIoU currently quoted in the research report, and that number
has to stay reproducible without regression risk.
"""
import os
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parent.parent.parent

# petroscope's global 50-class LumenStone codebook (petroscope/segmentation/
# lumenstone.yaml), shared across S1/S2/S3. Codes are therefore NON-CONTIGUOUS
# within any one subset and are remapped to a dense 0..N-1 only at tensor-build
# time for CrossEntropyLoss. Held in petroscope's own numbering and colours so our
# masks and figures stay directly comparable to the published ones.
CODEBOOK = {
    0: ("background", "#000000"),
    1: ("chalcopyrite", "#ffa500"),
    2: ("galena", "#9acd32"),
    3: ("magnetite", "#ff4500"),
    4: ("bornite", "#00bfff"),
    5: ("pyrrhotite", "#a9a9a9"),
    6: ("pyrite", "#2f4f4f"),
    7: ("pentlandite", "#ffff00"),
    8: ("sphalerite", "#ee82ee"),
    9: ("arsenopyrite", "#556b2f"),
    10: ("hematite", "#a0522d"),
    11: ("tennantite", "#483d8b"),
    12: ("covellite", "#008000"),
}

# Which codes each subset actually contains, verified by scanning its masks
# rather than taken from the website description.
SUBSET_CODES = {
    "S2": [0, 1, 3, 5, 7],              # Norilsk layered ultramafic Ni-Cu-PGE
    "S1": [0, 1, 2, 4, 6, 8, 11],       # Berezovskoe polymetallic hydrothermal
    # S3 v1: high-temperature hydrothermal. The website advertises 9 classes;
    # scanning the masks found ELEVEN codes present, so this list comes from the
    # data and not the description. Two things to know before reporting S3:
    #   - magnetite (0.64%) and hematite (0.27%) BOTH occur, which is the pair
    #     SEM/BSE cannot separate. S3 therefore lets us TEST the optical argument
    #     in report section 3 instead of asserting it.
    #   - tennantite is 0.006% of pixels, roughly 6 in every 100,000. It cannot
    #     reasonably be learned and will drag mean IoU down; report per-class and
    #     say so rather than quietly dropping the class.
    "S3": [0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 12],
}

# S3 uses v1: v2 is 5.2 GB because it adds XPL ROTATIONS of the same sections.
# Rotations are near-duplicates, so a naive split would leak them across
# train/test - the exact failure that made our MUMDMC numbers worthless. v1 has
# no rotations, so an image-level split is legitimate.
SUBSET_VERSION = {"S1": "v2", "S2": "v2", "S3": "v1"}

# Active subset, selected by environment variable so that switching experiments
# requires no code edit and, critically, so the default is unchanged: every S2
# result in the report reproduces exactly when KHANYA_SUBSET is unset.
# Checkpoint directories and metrics filenames all carry the subset name, so an
# S1 run cannot overwrite an S2 result.
SUBSET = os.environ.get("KHANYA_SUBSET", "S2").upper()
if SUBSET not in SUBSET_CODES:
    raise ValueError(f"KHANYA_SUBSET={SUBSET!r}; expected one of {list(SUBSET_CODES)}")

DATA_DIR = ROOT / "data" / "raw" / "lumenstone" / f"{SUBSET}_{SUBSET_VERSION[SUBSET]}"
S2_DIR = DATA_DIR  # backwards-compatible alias; prefer DATA_DIR in new code

CLASS_CODES = SUBSET_CODES[SUBSET]
CLASS_NAMES = [CODEBOOK[c][0] for c in CLASS_CODES]
CLASS_COLORS = [CODEBOOK[c][1] for c in CLASS_CODES]
NUM_CLASSES = len(CLASS_CODES)

# Base-metal sulphides, in contiguous index space. These carry the PGM payload
# in the Bushveld analogue and are the classes the advisor cares about.
BMS_INDICES = [1, 3, 4]  # chalcopyrite, pyrrhotite, pentlandite

# Source images are 3396x2547 (4:3). Resized rather than square-cropped so
# grain aspect is not distorted; both dims divisible by 16 for the ResNet
# output stride. Patch-based sampling at native resolution is the planned
# upgrade — petroscope's authors report it matters for the rare classes.
IMAGE_HW = (512, 688)

BATCH_SIZE = 2
EPOCHS = 12
LR = 1e-3
SEED = 42

# Authors ship train/ and test/ only. test/ is never touched during development;
# val is carved out of train so the held-out number stays honest.
VAL_COUNT = 6

_LOOKUP = torch.full((max(CLASS_CODES) + 1,), 255, dtype=torch.uint8)
for _index, _code in enumerate(CLASS_CODES):
    _LOOKUP[_code] = _index


def split_ids(seed: int = SEED):
    train = sorted(p.stem for p in (S2_DIR / "imgs" / "train").glob("*.jpg"))
    test = sorted(p.stem for p in (S2_DIR / "imgs" / "test").glob("*.jpg"))
    if not train:
        raise FileNotFoundError(
            f"No images under {S2_DIR / 'imgs' / 'train'}. See DATA-SOURCES.md Section 1."
        )
    rng = random.Random(seed)
    rng.shuffle(train)
    return train[VAL_COUNT:], train[:VAL_COUNT], test


class LumenStoneS2(Dataset):
    def __init__(self, ids, subdir: str, train: bool):
        self.ids = ids
        self.subdir = subdir
        self.train = train
        self.resize_image = transforms.Resize(
            IMAGE_HW, interpolation=transforms.InterpolationMode.BILINEAR
        )
        self.resize_mask = transforms.Resize(
            IMAGE_HW, interpolation=transforms.InterpolationMode.NEAREST
        )

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, index):
        stem = self.ids[index]
        image = Image.open(S2_DIR / "imgs" / self.subdir / f"{stem}.jpg").convert("RGB")
        mask = Image.open(S2_DIR / "masks" / self.subdir / f"{stem}.png")

        image = self.resize_image(image)
        mask = self.resize_mask(mask)

        # No colour jitter: reflectance and colour are the diagnostic signal in
        # reflected light, which is the whole optical-over-SEM argument.
        # Flips are safe — a polished section has no canonical orientation.
        if self.train and random.random() < 0.5:
            image = transforms.functional.hflip(image)
            mask = transforms.functional.hflip(mask)
        if self.train and random.random() < 0.5:
            image = transforms.functional.vflip(image)
            mask = transforms.functional.vflip(mask)

        image_t = transforms.functional.normalize(
            transforms.functional.to_tensor(image),
            (0.485, 0.456, 0.406), (0.229, 0.224, 0.225),
        )

        # Label is replicated across R, G and B — take one channel.
        codes = torch.from_numpy(np.array(mask, dtype=np.uint8))
        if codes.ndim == 3:
            codes = codes[:, :, 0]
        labels = _LOOKUP[codes.long()]
        if (labels == 255).any():
            unexpected = sorted(set(codes[labels == 255].flatten().tolist()))
            raise ValueError(f"{stem}: mask codes {unexpected} not in CLASS_CODES")
        return image_t, labels.long()


def preprocess(image):
    """PIL image -> normalised 1x3xHxW tensor, identical to the eval transform.

    Shared with the dashboard so inference at demo time cannot silently drift
    from inference at evaluation time.
    """
    resized = transforms.functional.resize(
        image, list(IMAGE_HW), interpolation=transforms.InterpolationMode.BILINEAR
    )
    normalised = transforms.functional.normalize(
        transforms.functional.to_tensor(resized),
        (0.485, 0.456, 0.406), (0.229, 0.224, 0.225),
    )
    return normalised.unsqueeze(0)


def build_loaders(batch_size: int = BATCH_SIZE):
    train_ids, val_ids, test_ids = split_ids()
    make = lambda ids, subdir, train: DataLoader(
        LumenStoneS2(ids, subdir, train),
        batch_size=batch_size,
        shuffle=train,
        num_workers=0,
        # drop_last on train only: a size-1 final batch crashes BatchNorm.
        drop_last=train,
    )
    return (
        make(train_ids, "train", True),
        make(val_ids, "train", False),
        make(test_ids, "test", False),
    )


def class_pixel_shares(ids=None, subdir="train"):
    """Pixel share per class. Imbalance here is the headline methodological
    risk, so it should be printable rather than folklore."""
    if ids is None:
        ids, _, _ = split_ids()
    counts = torch.zeros(NUM_CLASSES, dtype=torch.float64)
    for stem in ids:
        codes = torch.from_numpy(
            np.array(Image.open(S2_DIR / "masks" / subdir / f"{stem}.png"), dtype=np.uint8)
        )
        if codes.ndim == 3:
            codes = codes[:, :, 0]
        labels = _LOOKUP[codes.long()]
        counts += torch.bincount(labels.flatten().long(), minlength=NUM_CLASSES)
    return (counts / counts.sum()).tolist()


if __name__ == "__main__":
    train_ids, val_ids, test_ids = split_ids()
    print(f"train {len(train_ids)}  val {len(val_ids)}  test {len(test_ids)}")
    for name, share in zip(CLASS_NAMES, class_pixel_shares(train_ids)):
        print(f"  {name:14s} {share:7.2%}")
