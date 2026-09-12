"""IoU and pixel accuracy, matching the metric convention used in the LumenStone
/ petroscope benchmarks we're comparing against."""
import torch


def void_border_mask(target, border_width: int):
    """Valid-pixel mask matching petroscope's `void_borders`, so our numbers are
    comparable to the published LumenStone benchmark.

    Their protocol erodes each class's binary mask by a border_width square
    element and takes the union of the results as the evaluated region. Pixels
    within roughly border_width/2 of any class boundary are therefore excluded.

    The rationale is annotation ambiguity: a hand-drawn grain boundary is
    uncertain to within a few pixels, so scoring those pixels measures the
    annotator's pen as much as the model. It does inflate IoU, which is exactly
    why petroscope publish both columns and why we must state which one we quote.
    """
    import numpy as np
    from scipy import ndimage

    array = target.cpu().numpy() if hasattr(target, "cpu") else np.asarray(target)
    element = np.ones((border_width, border_width))
    valid = np.zeros(array.shape, dtype=np.uint8)
    for value in np.unique(array):
        valid += ndimage.binary_erosion(
            array == value, structure=element, border_value=0
        )
    return torch.from_numpy(valid > 0)


def confusion_from_batch(pred, target, num_classes, confusion, valid=None):
    """Accumulate into a dataset-wide confusion matrix.

    Dataset-wide accumulation, not a per-image average, matching petroscope's
    stated requirement that metrics use object areas across the whole dataset
    rather than within individual images. A per-image mean would let a section
    containing three pixels of a rare phase weigh as heavily as one containing
    thirty thousand.
    """
    for c_true in range(num_classes):
        for c_pred in range(num_classes):
            hit = (target == c_true) & (pred == c_pred)
            if valid is not None:
                hit = hit & valid
            confusion[c_true, c_pred] += hit.sum().item()
    return confusion


def summarise(confusion):
    """IoU/pixel-accuracy plus the per-class confusion counts the 2026-09-12
    review's accuracy-report template asks for (TP/FP/FN/recall/precision) -
    added here rather than recomputed elsewhere so there is exactly one place
    that reads the confusion matrix.

    Recall and precision are NaN, not zero, when their denominator is zero
    (no ground-truth pixels for recall; no predicted pixels for precision) -
    a class absent from both truth and prediction has no defined rate, and
    reporting zero would misstate a model that correctly never predicted it.
    """
    num_classes = confusion.shape[0]
    ious, pixel_acc_num, pixel_acc_den = [], 0.0, 0.0
    tp_list, fp_list, fn_list, recall_list, precision_list = [], [], [], [], []
    for c in range(num_classes):
        tp = confusion[c, c]
        fp = confusion[:, c].sum() - tp
        fn = confusion[c, :].sum() - tp
        denom = tp + fp + fn
        ious.append((tp / denom).item() if denom > 0 else float("nan"))
        pixel_acc_num += tp
        pixel_acc_den += confusion[c, :].sum()
        tp_list.append(int(tp))
        fp_list.append(int(fp))
        fn_list.append(int(fn))
        recall_list.append((tp / (tp + fn)).item() if (tp + fn) > 0 else float("nan"))
        precision_list.append((tp / (tp + fp)).item() if (tp + fp) > 0 else float("nan"))
    return {
        "iou_per_class": ious,
        "mean_iou": sum(v for v in ious if v == v) / len([v for v in ious if v == v]),
        "pixel_accuracy": (pixel_acc_num / pixel_acc_den).item(),
        "tp_per_class": tp_list,
        "fp_per_class": fp_list,
        "fn_per_class": fn_list,
        "recall_per_class": recall_list,
        "precision_per_class": precision_list,
    }


def new_confusion(num_classes=2):
    return torch.zeros(num_classes, num_classes, dtype=torch.float64)


def json_safe(summary):
    """summarise()'s NaN (an undefined rate, e.g. precision for a class the
    model never predicted) is a real Python float, valid input to Python's
    own json.dump - but a bare `NaN` token is not standard JSON, and a strict
    reader (JS's JSON.parse, jq, most non-Python tooling) will fail to parse
    a report written without this. Convert to null before writing any
    report to disk; keep using the NaN-valued dict returned by summarise()
    for in-process arithmetic, where NaN's "any comparison is false"
    behaviour is what the mean_iou/aggregate logic here already relies on.
    """
    return {
        key: [None if v != v else v for v in value] if isinstance(value, list) else value
        for key, value in summary.items()
    }
