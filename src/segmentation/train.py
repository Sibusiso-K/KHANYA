"""SUPERSEDED - kept only so the FeM binary ore/resin result this file
produced (mean IoU 0.872, reports/segmentation_test_metrics.json) stays
reproducible. It is a 2-class task and does not meet the brief's >=3 phase
floor. The live multi-class pipeline is lumenstone.py, train_lumenstone.py and
train_patches.py in this same directory. Do not build on this.
"""
import torch
from torch import nn
from tqdm import tqdm

from . import config, metrics
from .data import build_loaders
from .model import build_model, device


def run_epoch(model, loader, criterion, optimiser, dev, train: bool):
    model.train() if train else model.eval()
    total_loss, seen = 0.0, 0
    confusion = metrics.new_confusion()
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
            pred = out.argmax(1)
            metrics.confusion_from_batch(pred, masks, 2, confusion)
    summary = metrics.summarise(confusion)
    return total_loss / seen, summary


def main():
    torch.manual_seed(config.SEED)
    dev = device()
    print(f"device: {dev}")

    train_loader, val_loader, test_loader = build_loaders()
    print(f"train {len(train_loader.dataset)}  val {len(val_loader.dataset)}  "
          f"test {len(test_loader.dataset)}")

    model = build_model().to(dev)
    criterion = nn.CrossEntropyLoss()
    optimiser = torch.optim.AdamW(model.parameters(), lr=config.LR)

    config.CKPT_DIR.mkdir(parents=True, exist_ok=True)
    best_iou = 0.0
    for epoch in range(1, config.EPOCHS + 1):
        train_loss, train_summary = run_epoch(model, train_loader, criterion, optimiser, dev, True)
        val_loss, val_summary = run_epoch(model, val_loader, criterion, optimiser, dev, False)
        print(
            f"epoch {epoch:02d}  train loss {train_loss:.3f} mIoU {train_summary['mean_iou']:.3f}  "
            f"val loss {val_loss:.3f} mIoU {val_summary['mean_iou']:.3f} PA {val_summary['pixel_accuracy']:.3f}"
        )
        if val_summary["mean_iou"] > best_iou:
            best_iou = val_summary["mean_iou"]
            torch.save(model.state_dict(), config.CKPT_DIR / "best.pt")
            print(f"  saved (val mIoU {best_iou:.3f})")

    print(f"best val mean IoU: {best_iou:.3f}")


if __name__ == "__main__":
    main()
