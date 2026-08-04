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
    best_val = 0.0
    for epoch in range(1, config.EPOCHS + 1):
        train_loss, train_acc = run_epoch(
            model, train_loader, criterion, optimiser, dev, True
        )
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

    print(f"best val accuracy {best_val:.3f}")


if __name__ == "__main__":
    main()
