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
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parent.parent.parent
S2_DIR = ROOT / "data" / "raw" / "lumenstone" / "S2_v2"

# Codes are indices into petroscope's global 50-class LumenStone codebook
# (shared across S1/S2/S3), so they are non-contiguous. Held as-is for
# compatibility with petroscope's weights and visualisations, and remapped to a
# contiguous 0..4 only at tensor-build time for CrossEntropyLoss.
CLASS_CODES = [0, 1, 3, 5, 7]
CLASS_NAMES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]
NUM_CLASSES = len(CLASS_CODES)

# petroscope's own colours, kept so our visualisations are directly comparable
# to the published LumenStone figures.
CLASS_COLORS = ["#000000", "#ffa500", "#ff4500", "#a9a9a9", "#ffff00"]

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
