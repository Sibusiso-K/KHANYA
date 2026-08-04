"""Test-set evaluation. Everything the accuracy report claims comes from here."""
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix

from . import config
from .data import build_loaders
from .model import build_model, device


@torch.no_grad()
def predict(model, loader, dev):
    model.eval()
    true, pred = [], []
    for images, labels in loader:
        logits = model(images.to(dev))
        pred.extend(logits.argmax(1).cpu().tolist())
        true.extend(labels.tolist())
    return true, pred


def save_confusion(true, pred, path):
    matrix = confusion_matrix(true, pred, labels=range(len(config.CLASSES)))
    figure, axes = plt.subplots(figsize=(6, 5))
    axes.imshow(matrix, cmap="Blues")
    axes.set_xticks(range(len(config.CLASSES)), config.CLASSES, rotation=45, ha="right")
    axes.set_yticks(range(len(config.CLASSES)), config.CLASSES)
    axes.set_xlabel("predicted")
    axes.set_ylabel("true")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axes.text(j, i, matrix[i, j], ha="center", va="center")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    print(f"wrote {path}")
    # The hematite/magnetite cell is the one to talk about: SEM-BSE cannot
    # separate these two. If optical does, that is the headline result.


def main():
    dev = device()
    _, _, test_loader = build_loaders()

    model = build_model(pretrained=False).to(dev)
    model.load_state_dict(torch.load(config.CKPT_DIR / "best.pt", map_location=dev))

    true, pred = predict(model, test_loader, dev)

    config.REPORT_DIR.mkdir(exist_ok=True)
    report = classification_report(
        true, pred, target_names=config.CLASSES, output_dict=True, zero_division=0
    )
    frame = pd.DataFrame(report).transpose()
    frame.to_csv(config.REPORT_DIR / "classification_report.csv")
    print(frame.round(3).to_string())

    save_confusion(true, pred, config.REPORT_DIR / "confusion_matrix.png")


if __name__ == "__main__":
    main()
