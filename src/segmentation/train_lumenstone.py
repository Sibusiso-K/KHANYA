"""Train / evaluate multi-class segmentation on LumenStone S2.

    python -m src.segmentation.train_lumenstone          # train
    python -m src.segmentation.train_lumenstone --eval   # held-out test metrics

Report per-class IoU, never mean IoU alone: pyrrhotite is ~45% of pixels and
magnetite ~1.8%, so a mean is flattered by the phase that matters least. The
petroscope authors report that loss/class weighting does NOT fix this imbalance,
so the baseline deliberately uses plain cross-entropy — patch-based
self-balancing sampling is the intended fix, and claiming a weighting trick
solved it would not survive questioning.
"""
import argparse
import json

import torch
from torch import nn
from tqdm import tqdm

from . import config, lumenstone, metrics
from .model import build_model, device

CKPT_DIR = config.ROOT / "checkpoints" / "lumenstone_s2"
CKPT = CKPT_DIR / "best.pt"


def run_epoch(model, loader, criterion, optimiser, dev, train: bool):
    model.train() if train else model.eval()
    total_loss, seen = 0.0, 0
    confusion = metrics.new_confusion(lumenstone.NUM_CLASSES)
    with torch.set_grad_enabled(train):
        for images, masks in tqdm(loader, leave=False):
            images, masks = images.to(dev), masks.to(dev)
            out = model(images)["out"]
            loss = criterion(out, masks)
            if train:
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()
            total_loss += loss.item() * images.size(0)
            seen += images.size(0)
            metrics.confusion_from_batch(
                out.argmax(1), masks, lumenstone.NUM_CLASSES, confusion
            )
    return total_loss / seen, metrics.summarise(confusion)


def report(summary):
    lines = [f"  mean IoU {summary['mean_iou']:.4f}   "
             f"pixel accuracy {summary['pixel_accuracy']:.4f}"]
    for name, iou in zip(lumenstone.CLASS_NAMES, summary["iou_per_class"]):
        lines.append(f"    {name:14s} IoU {iou:.4f}")
    return "\n".join(lines)


def train():
    torch.manual_seed(lumenstone.SEED)
    dev = device()
    train_loader, val_loader, _ = build()
    print(f"device: {dev}")
    print(f"train {len(train_loader.dataset)}  val {len(val_loader.dataset)}")

    model = build_model(num_classes=lumenstone.NUM_CLASSES).to(dev)
    criterion = nn.CrossEntropyLoss()
    optimiser = torch.optim.AdamW(model.parameters(), lr=lumenstone.LR)

    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    best_iou = 0.0
    for epoch in range(1, lumenstone.EPOCHS + 1):
        train_loss, train_summary = run_epoch(
            model, train_loader, criterion, optimiser, dev, True
        )
        val_loss, val_summary = run_epoch(
            model, val_loader, criterion, optimiser, dev, False
        )
        print(
            f"epoch {epoch:02d}  train loss {train_loss:.3f} mIoU "
            f"{train_summary['mean_iou']:.3f}  |  val loss {val_loss:.3f}"
        )
        print(report(val_summary))
        if val_summary["mean_iou"] > best_iou:
            best_iou = val_summary["mean_iou"]
            torch.save(model.state_dict(), CKPT)
            print(f"  saved (val mIoU {best_iou:.4f})")

    print(f"best val mean IoU: {best_iou:.4f}")


@torch.no_grad()
def evaluate():
    dev = device()
    _, _, test_loader = build()
    model = build_model(num_classes=lumenstone.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(CKPT, map_location=dev))
    model.eval()

    confusion = metrics.new_confusion(lumenstone.NUM_CLASSES)
    for images, masks in tqdm(test_loader, leave=False):
        images, masks = images.to(dev), masks.to(dev)
        pred = model(images)["out"].argmax(1)
        metrics.confusion_from_batch(pred, masks, lumenstone.NUM_CLASSES, confusion)

    summary = metrics.summarise(confusion)
    summary["class_names"] = lumenstone.CLASS_NAMES
    summary["train_pixel_shares"] = lumenstone.class_pixel_shares()
    summary["n_test_images"] = len(test_loader.dataset)

    print(f"held-out test set ({summary['n_test_images']} images, never seen):")
    print(report(summary))

    config.REPORT_DIR.mkdir(exist_ok=True)
    out = config.REPORT_DIR / "lumenstone_s2_test_metrics.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {out}")


def build():
    return lumenstone.build_loaders()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", action="store_true")
    evaluate() if parser.parse_args().eval else train()
