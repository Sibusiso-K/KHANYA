"""Train / evaluate the patch-based native-resolution model on LumenStone S2.

    python -m src.segmentation.train_patches          # train
    python -m src.segmentation.train_patches --eval   # held-out test, full sections

Kept separate from train_lumenstone.py so the resize baseline (mIoU 0.545,
magnetite 0.000) stays reproducible - the whole point is a controlled comparison
between the two, and that is worthless if the baseline drifts.

Evaluation is deliberately NOT patch-based: it runs sliding-window inference over
whole native-resolution sections, so the number is directly comparable to the
resize baseline's, which also scored whole sections. Scoring on balanced patches
instead would flatter the rare classes by construction and would not be an
honest comparison.
"""
import argparse
import json

import numpy as np
import torch
from PIL import Image
from torch import nn
from tqdm import tqdm

from . import config, losses, lumenstone as ls, metrics, patches
from .model import build_model, device

CKPT_DIR = config.ROOT / "checkpoints" / f"lumenstone_{ls.SUBSET.lower()}_patches"
CKPT = CKPT_DIR / "best.pt"


def checkpoint_for(loss_name: str):
    """Each loss gets its own checkpoint directory. Runs must never clobber each
    other's weights - the whole value here is a controlled comparison, and an
    evaluation reading a checkpoint while another run overwrites it is a silent
    way to produce nonsense."""
    if loss_name == "ce":
        return CKPT
    return (config.ROOT / "checkpoints"
            / f"lumenstone_{ls.SUBSET.lower()}_patches_{loss_name}" / "best.pt")


def run_epoch(model, loader, criterion, optimiser, dev, train: bool):
    model.train() if train else model.eval()
    total_loss, seen = 0.0, 0
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
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
            metrics.confusion_from_batch(out.argmax(1), masks, ls.NUM_CLASSES, confusion)
    return total_loss / max(seen, 1), metrics.summarise(confusion)


def report(summary):
    lines = [f"  mean IoU {summary['mean_iou']:.4f}   "
             f"pixel accuracy {summary['pixel_accuracy']:.4f}"]
    for name, iou, recall, precision in zip(
        ls.CLASS_NAMES, summary["iou_per_class"],
        summary["recall_per_class"], summary["precision_per_class"],
    ):
        lines.append(f"    {name:14s} IoU {iou:.4f}   "
                     f"recall {recall:.4f}   precision {precision:.4f}")
    return "\n".join(lines)


def train(loss_name="ce"):
    torch.manual_seed(patches.SEED)
    dev = device()
    checkpoint = checkpoint_for(loss_name)
    print(f"device: {dev}   loss: {loss_name}   checkpoint: {checkpoint}")
    train_loader, val_loader = patches.build_loaders()
    print(f"patches/epoch: train {patches.PATCHES_PER_EPOCH}  val {patches.VAL_PATCHES}"
          f"  size {patches.PATCH}px native  lr {patches.LR}")

    model = build_model(num_classes=ls.NUM_CLASSES).to(dev)
    criterion = losses.build_loss(loss_name, ls.NUM_CLASSES)
    optimiser = torch.optim.AdamW(model.parameters(), lr=patches.LR)

    checkpoint.parent.mkdir(parents=True, exist_ok=True)

    # Resume support. Long CPU runs on this machine have repeatedly been killed
    # when the controlling session exits, losing hours of work because the only
    # thing written was best.pt - and only on an improvement. last.pt is written
    # EVERY epoch with the optimiser state, so an interrupted run resumes at the
    # next epoch instead of restarting from scratch.
    resume_path = checkpoint.parent / "last.pt"
    best_iou, start_epoch = 0.0, 1
    if resume_path.exists():
        state = torch.load(resume_path, map_location=dev, weights_only=False)
        same_budget = (
            state.get("epochs") == patches.EPOCHS
            and state.get("patches_per_epoch") == patches.PATCHES_PER_EPOCH
        )
        if same_budget:
            model.load_state_dict(state["model"])
            optimiser.load_state_dict(state["optimiser"])
            best_iou = state["best_iou"]
            start_epoch = state["epoch"] + 1
            print(f"resuming at epoch {start_epoch} (best val mIoU {best_iou:.4f})")
        else:
            print("last.pt is from a different budget; starting fresh")

    for epoch in range(start_epoch, patches.EPOCHS + 1):
        train_loss, train_summary = run_epoch(
            model, train_loader, criterion, optimiser, dev, True
        )
        val_loss, val_summary = run_epoch(
            model, val_loader, criterion, optimiser, dev, False
        )
        print(f"epoch {epoch:02d}  train loss {train_loss:.3f} "
              f"mIoU {train_summary['mean_iou']:.3f}  |  val loss {val_loss:.3f}")
        print(report(val_summary))
        if val_summary["mean_iou"] > best_iou:
            best_iou = val_summary["mean_iou"]
            torch.save(model.state_dict(), checkpoint)
            print(f"  saved (val patch mIoU {best_iou:.4f})")
        torch.save({
            "model": model.state_dict(),
            "optimiser": optimiser.state_dict(),
            "epoch": epoch,
            "best_iou": best_iou,
            "epochs": patches.EPOCHS,
            "patches_per_epoch": patches.PATCHES_PER_EPOCH,
        }, resume_path)

    print(f"best val patch mean IoU: {best_iou:.4f}")
    print("NOTE: val here is balanced patches, so it is NOT comparable to the "
          "resize baseline's whole-section val. Use --eval for the real number.")


@torch.no_grad()
def evaluate(loss_name="ce"):
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(checkpoint_for(loss_name), map_location=dev))
    model.eval()

    _, _, test_ids = ls.split_ids()
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
    for stem in tqdm(sorted(test_ids), leave=False):
        image = Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg")
        predicted, _ = patches.sliding_window_predict(model, image, dev)
        truth = patches.labels_for(stem, "test")
        metrics.confusion_from_batch(
            torch.from_numpy(predicted), torch.from_numpy(truth),
            ls.NUM_CLASSES, confusion,
        )

    summary = metrics.summarise(confusion)
    summary["class_names"] = ls.CLASS_NAMES
    summary["n_test_images"] = len(test_ids)
    summary["method"] = (
        f"sliding window, {patches.PATCH}px patches at native resolution, "
        "whole sections, no downsampling"
    )
    print(f"held-out test set ({len(test_ids)} whole sections, native resolution):")
    print(report(summary))

    config.REPORT_DIR.mkdir(exist_ok=True)
    summary["loss"] = loss_name
    suffix = "" if loss_name == "ce" else f"_{loss_name}"
    out = config.REPORT_DIR / f"lumenstone_{ls.SUBSET.lower()}_patches{suffix}_test_metrics.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--loss", choices=("ce", "dice"), default="ce",
                        help="'dice' = cross-entropy + soft Dice; see losses.py")
    args = parser.parse_args()
    evaluate(args.loss) if args.eval else train(args.loss)
