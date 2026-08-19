"""SUPERSEDED - kept only so the FeM binary ore/resin result this file
produced (mean IoU 0.872, reports/segmentation_test_metrics.json) stays
reproducible. It is a 2-class task and does not meet the brief's >=3 phase
floor. The live multi-class pipeline is lumenstone.py, train_lumenstone.py and
train_patches.py in this same directory. Do not build on this.
"""
import json

import torch

from . import config, metrics
from .data import build_loaders
from .model import build_model, device


@torch.no_grad()
def main():
    dev = device()
    _, _, test_loader = build_loaders()

    model = build_model(pretrained=False).to(dev)
    model.load_state_dict(torch.load(config.CKPT_DIR / "best.pt", map_location=dev))
    model.eval()

    confusion = metrics.new_confusion()
    for images, masks in test_loader:
        images, masks = images.to(dev), masks.to(dev)
        pred = model(images)["out"].argmax(1)
        metrics.confusion_from_batch(pred, masks, 2, confusion)

    summary = metrics.summarise(confusion)
    print(json.dumps(summary, indent=2))

    config.REPORT_DIR.mkdir(exist_ok=True)
    with open(config.REPORT_DIR / "segmentation_test_metrics.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
