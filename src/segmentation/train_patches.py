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
import hashlib
import json
import os
import random

import numpy as np
import torch
from PIL import Image
from torch import nn
from tqdm import tqdm

from . import config, losses, lumenstone as ls, metrics, patches
from .model import build_model, device

DEFAULT_RUN_ID = f"s2-seed{patches.SEED}-fullval-v1"


def checkpoint_for(loss_name: str):
    """Each loss gets its own checkpoint directory. Runs must never clobber each
    other's weights - the whole value here is a controlled comparison, and an
    evaluation reading a checkpoint while another run overwrites it is a silent
    way to produce nonsense."""
    run_id = os.environ.get("KHANYA_RUN_ID", DEFAULT_RUN_ID)
    return (config.ROOT / "checkpoints"
            / f"lumenstone_{ls.SUBSET.lower()}_patches_{run_id}_{loss_name}" / "best.pt")


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


@torch.no_grad()
def evaluate_sections(model, image_ids, dev):
    """Pool metrics over complete native-resolution sections for model selection."""
    model.eval()
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
    per_section = {}
    for stem in tqdm(sorted(image_ids), desc="full-section validation", leave=False):
        with Image.open(ls.DATA_DIR / "imgs" / "train" / f"{stem}.jpg") as source:
            image = source.convert("RGB")
        predicted, _ = patches.sliding_window_predict(model, image, dev)
        truth = patches.labels_for(stem, "train")
        predicted_t, truth_t = torch.from_numpy(predicted), torch.from_numpy(truth)
        metrics.confusion_from_batch(predicted_t, truth_t, ls.NUM_CLASSES, confusion)
        section_confusion = metrics.new_confusion(ls.NUM_CLASSES)
        metrics.confusion_from_batch(
            predicted_t, truth_t, ls.NUM_CLASSES, section_confusion,
        )
        per_section[stem] = metrics.summarise(section_confusion)
    summary = metrics.summarise(confusion)
    summary["class_names"] = ls.CLASS_NAMES
    summary["n_validation_sections"] = len(image_ids)
    summary["per_section"] = per_section
    foreground_ious = [iou for iou in summary["iou_per_class"][1:] if iou == iou]
    summary["foreground_macro_iou"] = (
        sum(foreground_ious) / len(foreground_ious) if foreground_ious else float("nan")
    )
    if not foreground_ious:
        raise ValueError("Validation sections contain no evaluable foreground mineral pixels")
    summary["method"] = (
        f"sliding window, {patches.PATCH}px patches at native resolution, "
        "whole sections, no downsampling"
    )
    return summary


def train(loss_name="ce"):
    random.seed(patches.SEED)
    np.random.seed(patches.SEED)
    torch.manual_seed(patches.SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(patches.SEED)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
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
    history_path = checkpoint.parent / "validation_history.json"
    best_iou, start_epoch = float("-inf"), 1
    validation_history = []
    train_ids, val_ids, _ = ls.split_ids()
    config_signature = {
        "selection_metric": "full_section_validation_foreground_macro_iou",
        "loss": loss_name,
        "seed": patches.SEED,
        "epochs": patches.EPOCHS,
        "patches_per_epoch": patches.PATCHES_PER_EPOCH,
        "validation_patches": patches.VAL_PATCHES,
        "patch_size": patches.PATCH,
        "learning_rate": patches.LR,
        "train_ids": sorted(train_ids),
        "validation_ids": sorted(val_ids),
    }
    if resume_path.exists():
        state = torch.load(resume_path, map_location=dev, weights_only=False)
        if state.get("config_signature") != config_signature:
            raise RuntimeError(
                "last.pt belongs to another run configuration; choose a fresh "
                "KHANYA_RUN_ID instead of overwriting that run"
            )
        model.load_state_dict(state["model"])
        optimiser.load_state_dict(state["optimiser"])
        best_iou = state["best_validation_foreground_macro_iou"]
        start_epoch = state["epoch"] + 1
        validation_history = state.get("validation_history", [])
        print(f"resuming at epoch {start_epoch} "
                  f"(best full-section foreground macro IoU {best_iou:.4f})")
    elif checkpoint.exists():
        raise RuntimeError(
            "checkpoint exists without matching resume state; choose a fresh "
            "KHANYA_RUN_ID to avoid keeping a stale best checkpoint"
        )

    for epoch in range(start_epoch, patches.EPOCHS + 1):
        train_loader.dataset.set_epoch(epoch)
        train_loss, train_summary = run_epoch(
            model, train_loader, criterion, optimiser, dev, True
        )
        val_loss, val_summary = run_epoch(
            model, val_loader, criterion, optimiser, dev, False
        )
        full_val_summary = evaluate_sections(model, val_loader.dataset.ids, dev)
        print(f"epoch {epoch:02d}  train loss {train_loss:.3f} "
              f"train patch mIoU {train_summary['mean_iou']:.3f}  |  "
              f"patch val loss {val_loss:.3f}")
        print(f"balanced patch validation (diagnostic only):\n{report(val_summary)}")
        print(f"full-section validation (checkpoint selection):\n{report(full_val_summary)}")
        print(f"foreground macro IoU: {full_val_summary['foreground_macro_iou']:.4f}")
        selected_for_checkpoint = full_val_summary["foreground_macro_iou"] > best_iou
        if selected_for_checkpoint:
            best_iou = full_val_summary["foreground_macro_iou"]
            torch.save(model.state_dict(), checkpoint)
            print(f"  saved (full-section foreground macro IoU {best_iou:.4f})")
        validation_history.append({
            "epoch": epoch,
            "train_patch_loss": train_loss,
            "train_patch_metrics": train_summary,
            "validation_patch_loss": val_loss,
            "validation_patch_metrics": val_summary,
            "validation_full_section_metrics": full_val_summary,
            "selected_for_checkpoint": selected_for_checkpoint,
        })
        torch.save({
            "model": model.state_dict(),
            "optimiser": optimiser.state_dict(),
            "epoch": epoch,
            "best_validation_foreground_macro_iou": best_iou,
            "config_signature": config_signature,
            "validation_history": validation_history,
        }, resume_path)
        temp_history_path = history_path.with_suffix(".tmp")
        temp_history_path.write_text(
            json.dumps(metrics.json_safe(validation_history), indent=2), encoding="utf-8",
        )
        temp_history_path.replace(history_path)

    print(f"best full-section validation foreground macro IoU: {best_iou:.4f}")
    print(f"full-section validation history: {history_path}")


@torch.no_grad()
def evaluate(loss_name="ce"):
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.load_state_dict(torch.load(checkpoint_for(loss_name), map_location=dev))
    model.eval()

    # Per-image breakdown alongside the pooled matrix, not instead of it: the
    # 2026-09-12 review's accuracy-report template asks for a locality-level
    # split, which LumenStone's archive does not ship metadata to build (no
    # locality/specimen manifest exists in the distributed data - confirmed
    # by inspection, not assumed). Per-image is the coarser breakdown that
    # IS buildable from what we have, and it is a real step towards it: test
    # image != locality, but a pooled dataset-wide number currently hides
    # whether performance is uniform or concentrated in a few hard sections.
    _, _, test_ids = ls.split_ids()
    confusion = metrics.new_confusion(ls.NUM_CLASSES)
    per_image = {}
    for stem in tqdm(sorted(test_ids), leave=False):
        image = Image.open(ls.DATA_DIR / "imgs" / "test" / f"{stem}.jpg")
        predicted, _ = patches.sliding_window_predict(model, image, dev)
        truth = patches.labels_for(stem, "test")
        pred_t, truth_t = torch.from_numpy(predicted), torch.from_numpy(truth)
        metrics.confusion_from_batch(pred_t, truth_t, ls.NUM_CLASSES, confusion)
        image_confusion = metrics.new_confusion(ls.NUM_CLASSES)
        metrics.confusion_from_batch(pred_t, truth_t, ls.NUM_CLASSES, image_confusion)
        per_image[stem] = metrics.summarise(image_confusion)

    summary = metrics.summarise(confusion)
    summary["class_names"] = ls.CLASS_NAMES
    summary["n_test_images"] = len(test_ids)
    summary["per_image"] = per_image
    summary["per_image_note"] = (
        "Per test image, not per locality - LumenStone ships no "
        "locality/specimen manifest to group by. Do not treat a test image "
        "as an independent locality when computing a cluster-robust "
        "interval; see the 2026-09-12 review's accuracy-report template."
    )
    summary["method"] = (
        f"sliding window, {patches.PATCH}px patches at native resolution, "
        "whole sections, no downsampling"
    )
    print(f"held-out test set ({len(test_ids)} whole sections, native resolution):")
    print(report(summary))

    config.REPORT_DIR.mkdir(exist_ok=True)
    summary["loss"] = loss_name
    summary["run_id"] = os.environ.get("KHANYA_RUN_ID", DEFAULT_RUN_ID)
    run_id = os.environ.get("KHANYA_RUN_ID", DEFAULT_RUN_ID)
    suffix = "" if loss_name == "ce" else f"_{loss_name}"
    out = config.REPORT_DIR / (
        f"lumenstone_{ls.SUBSET.lower()}_patches_{run_id}{suffix}_test_metrics.json"
    )
    summary["checkpoint_sha256"] = hashlib.sha256(checkpoint_for(loss_name).read_bytes()).hexdigest()
    with open(out, "w") as f:
        json.dump(metrics.json_safe(summary), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--loss", choices=("ce", "dice"), default="ce",
                        help="'dice' = cross-entropy + soft Dice; see losses.py")
    args = parser.parse_args()
    evaluate(args.loss) if args.eval else train(args.loss)
