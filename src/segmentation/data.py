import random

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from . import config


def pair_ids():
    """FeM filenames: FeM_NNN_RLM.tif / FeM_NNN_Ref.tif."""
    ids = sorted(p.stem.replace("_RLM", "") for p in config.IMAGE_DIR.glob("*_RLM.tif"))
    if not ids:
        raise FileNotFoundError(f"No image/mask pairs under {config.IMAGE_DIR}")
    return ids


def split_ids(seed: int = config.SEED):
    ids = pair_ids()
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_val = max(1, round(len(ids) * config.VAL_FRACTION))
    n_test = max(1, round(len(ids) * config.TEST_FRACTION))
    val_ids = ids[:n_val]
    test_ids = ids[n_val:n_val + n_test]
    train_ids = ids[n_val + n_test:]
    return train_ids, val_ids, test_ids


class FeMDataset(Dataset):
    def __init__(self, ids, train: bool):
        self.ids = ids
        self.train = train
        self.resize_img = transforms.Resize(
            (config.IMAGE_SIZE, config.IMAGE_SIZE),
            interpolation=transforms.InterpolationMode.BILINEAR,
        )
        self.resize_mask = transforms.Resize(
            (config.IMAGE_SIZE, config.IMAGE_SIZE),
            interpolation=transforms.InterpolationMode.NEAREST,
        )

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, index):
        stem = self.ids[index]
        image = Image.open(config.IMAGE_DIR / f"{stem}_RLM.tif").convert("RGB")
        mask = Image.open(config.MASK_DIR / f"{stem}_Ref.tif")

        image = self.resize_img(image)
        mask = self.resize_mask(mask)

        if self.train and random.random() < 0.5:
            image = transforms.functional.hflip(image)
            mask = transforms.functional.hflip(mask)
        if self.train and random.random() < 0.5:
            image = transforms.functional.vflip(image)
            mask = transforms.functional.vflip(mask)

        image_t = transforms.functional.to_tensor(image)
        image_t = transforms.functional.normalize(
            image_t, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
        )
        mask_t = torch.from_numpy((np.array(mask) > 127).astype("int64"))
        return image_t, mask_t


def build_loaders():
    train_ids, val_ids, test_ids = split_ids()
    make = lambda ids, train: DataLoader(
        FeMDataset(ids, train), batch_size=config.BATCH_SIZE, shuffle=train, num_workers=0
    )
    return make(train_ids, True), make(val_ids, False), make(test_ids, False)


if __name__ == "__main__":
    train_ids, val_ids, test_ids = split_ids()
    print(f"train {len(train_ids)}  val {len(val_ids)}  test {len(test_ids)}")
