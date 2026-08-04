"""Dataset and specimen-level splitting.

The single most important thing in this file: images from one physical specimen
must never appear in more than one split. Rotations of the same polished section
are near-duplicates; a random per-image split leaks them across train and test and
reports an accuracy that will not survive a judge's question.
"""
import random
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from . import config


def specimen_id_from_path(path: Path) -> str:
    """Specimen id = filename up to the first underscore.

    Adapt this to the dataset's naming. If a dataset gives no specimen id at all,
    say so in the report rather than silently falling back to a random split.
    """
    return path.stem.split("_")[0]


def index_images(raw_dir: Path = config.RAW_DIR):
    """Return [(path, label_index, specimen_id)] for every image found."""
    items = []
    for label_index, class_name in enumerate(config.CLASSES):
        class_dir = raw_dir / class_name
        if not class_dir.is_dir():
            raise FileNotFoundError(
                f"Missing class directory {class_dir}. See data/README.md."
            )
        for path in sorted(class_dir.rglob("*")):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
                items.append((path, label_index, specimen_id_from_path(path)))
    if not items:
        raise FileNotFoundError(f"No images under {raw_dir}. See data/README.md.")
    return items


def split_by_specimen(items, seed: int = config.SEED):
    """Group-aware split. Returns (train, val, test) lists of items."""
    specimens = sorted({specimen for _, _, specimen in items})
    rng = random.Random(seed)
    rng.shuffle(specimens)

    n_val = max(1, round(len(specimens) * config.VAL_FRACTION))
    n_test = max(1, round(len(specimens) * config.TEST_FRACTION))
    if n_val + n_test >= len(specimens):
        raise ValueError(
            f"Only {len(specimens)} specimens found - too few for a clean "
            "group split. Get more specimens before trusting any accuracy number."
        )

    val_set = set(specimens[:n_val])
    test_set = set(specimens[n_val:n_val + n_test])

    train = [i for i in items if i[2] not in val_set and i[2] not in test_set]
    val = [i for i in items if i[2] in val_set]
    test = [i for i in items if i[2] in test_set]
    return train, val, test


def build_transforms(train: bool):
    """Colour is diagnostic in reflected light, so no colour jitter on hue.

    Rotation and flips are safe: a polished section has no canonical orientation.
    """
    steps = [transforms.Resize((config.IMAGE_SIZE, config.IMAGE_SIZE))]
    if train:
        steps += [
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(180),
        ]
    steps += [
        transforms.ToTensor(),
        transforms.Normalize(config.NORM_MEAN, config.NORM_STD),
    ]
    return transforms.Compose(steps)


class MineralDataset(Dataset):
    def __init__(self, items, train: bool):
        self.items = items
        self.transform = build_transforms(train)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        path, label, _ = self.items[index]
        image = Image.open(path).convert("RGB")
        return self.transform(image), label


def build_loaders(batch_size: int = config.BATCH_SIZE):
    train_items, val_items, test_items = split_by_specimen(index_images())
    make = lambda items, train: DataLoader(
        MineralDataset(items, train),
        batch_size=batch_size,
        shuffle=train,
        num_workers=0,  # 0 avoids Windows multiprocessing pain; raise on Linux
    )
    return make(train_items, True), make(val_items, False), make(test_items, False)


def summarise_split():
    """Print split sizes so leakage assumptions are visible, not implicit."""
    train, val, test = split_by_specimen(index_images())
    for name, part in (("train", train), ("val", val), ("test", test)):
        specimens = len({s for _, _, s in part})
        print(f"{name:5s} {len(part):5d} images  {specimens:3d} specimens")


if __name__ == "__main__":
    summarise_split()
