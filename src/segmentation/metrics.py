"""IoU and pixel accuracy, matching the metric convention used in the LumenStone
/ petroscope benchmarks we're comparing against."""
import torch


def confusion_from_batch(pred, target, num_classes, confusion):
    for c_true in range(num_classes):
        for c_pred in range(num_classes):
            confusion[c_true, c_pred] += (
                (target == c_true) & (pred == c_pred)
            ).sum().item()
    return confusion


def summarise(confusion):
    num_classes = confusion.shape[0]
    ious, pixel_acc_num, pixel_acc_den = [], 0.0, 0.0
    for c in range(num_classes):
        tp = confusion[c, c]
        fp = confusion[:, c].sum() - tp
        fn = confusion[c, :].sum() - tp
        denom = tp + fp + fn
        ious.append((tp / denom).item() if denom > 0 else float("nan"))
        pixel_acc_num += tp
        pixel_acc_den += confusion[c, :].sum()
    return {
        "iou_per_class": ious,
        "mean_iou": sum(v for v in ious if v == v) / len([v for v in ious if v == v]),
        "pixel_accuracy": (pixel_acc_num / pixel_acc_den).item(),
    }


def new_confusion(num_classes=2):
    return torch.zeros(num_classes, num_classes, dtype=torch.float64)
