import torch
from torch import nn
from tqdm import tqdm

from . import config
from .data import build_loaders
from .model import build_model, device


def run_epoch(model, loader, criterion, optimiser, dev, train: bool):
    model.train() if train else model.eval()
    total_loss, correct, seen = 0.0, 0, 0
    with torch.set_grad_enabled(train):
        for images, labels in tqdm(loader, leave=False):
            images, labels = images.to(dev), labels.to(dev)
            logits = model(images)
            loss = criterion(logits, labels)
            if train:
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()
            total_loss += loss.item() * labels.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            seen += labels.size(0)
    return total_loss / seen, correct / seen


def main():
    torch.manual_seed(config.SEED)
    dev = device()
    print(f"device: {dev}")

    train_loader, val_loader, _ = build_loaders()
    model = build_model().to(dev)
    criterion = nn.CrossEntropyLoss()
    optimiser = torch.optim.AdamW(
        model.parameters(), lr=config.LR, weight_decay=config.WEIGHT_DECAY
    )

    config.CKPT_DIR.mkdir(exist_ok=True)
    has_val = len(val_loader.dataset) > 0
    if not has_val:
        print(
            "NOTE: no held-out specimens for this dataset (too few specimens "
            "per class). Training as a PIPELINE SANITY CHECK only - the "
            "numbers below are train-set fit, not a generalisation estimate. "
            "Do not report this as accuracy in the deliverable."
        )

    best_val = 0.0
    for epoch in range(1, config.EPOCHS + 1):
        train_loss, train_acc = run_epoch(
            model, train_loader, criterion, optimiser, dev, True
        )
        if has_val:
            val_loss, val_acc = run_epoch(
                model, val_loader, criterion, optimiser, dev, False
            )
            print(
                f"epoch {epoch:02d}  train {train_loss:.3f}/{train_acc:.3f}  "
                f"val {val_loss:.3f}/{val_acc:.3f}"
            )
            if val_acc > best_val:
                best_val = val_acc
                torch.save(model.state_dict(), config.CKPT_DIR / "best.pt")
                print(f"  saved (val acc {val_acc:.3f})")
        else:
            print(f"epoch {epoch:02d}  train {train_loss:.3f}/{train_acc:.3f}")

    if not has_val:
        torch.save(model.state_dict(), config.CKPT_DIR / "best.pt")
        print(f"final train accuracy (NOT a generalisation estimate): {train_acc:.3f}")
    else:
        print(f"best val accuracy {best_val:.3f}")


if __name__ == "__main__":
    main()
