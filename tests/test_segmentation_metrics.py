"""summarise()'s confusion-matrix arithmetic, pinned against a hand-worked
3-class example - added when the 2026-09-12 review's accuracy-report template
needed real TP/FP/FN/recall/precision, not just IoU and pixel accuracy.
"""
import json

import torch

from src.segmentation.metrics import json_safe, summarise


def _confusion_from_pairs(pairs, num_classes=3):
    """Build a confusion matrix directly from (truth, pred) pixel pairs,
    bypassing confusion_from_batch so the hand-worked numbers below are easy
    to check by eye."""
    confusion = torch.zeros(num_classes, num_classes, dtype=torch.float64)
    for truth, pred in pairs:
        confusion[truth, pred] += 1
    return confusion


class TestSummarise:
    def test_a_hand_worked_three_class_example(self):
        # Class 0: 3 correct, 1 predicted as class 1 (a false negative for 0,
        # false positive for 1). Class 1: 2 correct. Class 2: never appears in
        # truth or prediction at all.
        pairs = [(0, 0), (0, 0), (0, 0), (0, 1), (1, 1), (1, 1)]
        summary = summarise(_confusion_from_pairs(pairs))

        assert summary["tp_per_class"] == [3, 2, 0]
        assert summary["fp_per_class"] == [0, 1, 0]
        assert summary["fn_per_class"] == [1, 0, 0]

        # Recall: TP / (TP + FN). Class 0 missed one of its four true pixels.
        assert summary["recall_per_class"][0] == 3 / 4
        assert summary["recall_per_class"][1] == 1.0
        # Class 2 has zero ground-truth pixels - recall is undefined, not zero.
        assert summary["recall_per_class"][2] != summary["recall_per_class"][2]  # NaN

        # Precision: TP / (TP + FP). Class 1 predicted 3 pixels, 2 correct.
        assert summary["precision_per_class"][0] == 1.0
        assert summary["precision_per_class"][1] == 2 / 3
        # Class 2 was never predicted - precision is undefined, not zero.
        assert summary["precision_per_class"][2] != summary["precision_per_class"][2]

    def test_a_class_absent_from_truth_and_prediction_does_not_break_iou(self):
        """The pre-existing mean_iou behaviour (skip NaN classes) must survive
        the new fields being added alongside it."""
        pairs = [(0, 0), (1, 1)]
        summary = summarise(_confusion_from_pairs(pairs))
        assert summary["mean_iou"] == 1.0


class TestJsonSafe:
    def test_nan_becomes_null_so_the_report_is_strict_json(self):
        """A bare NaN token is valid input to Python's own json.dump but is
        not standard JSON - a stricter reader (JS's JSON.parse, jq) fails to
        parse it. Every report written to disk must go through this first."""
        pairs = [(0, 0)]  # class 1 never appears in truth or prediction
        summary = summarise(_confusion_from_pairs(pairs, num_classes=2))
        assert summary["precision_per_class"][1] != summary["precision_per_class"][1]

        safe = json_safe(summary)
        assert safe["precision_per_class"][1] is None
        # Must not silently corrupt a real, defined value.
        assert safe["precision_per_class"][0] == 1.0

        dumped = json.dumps(safe)
        assert "NaN" not in dumped
        assert json.loads(dumped)["precision_per_class"][1] is None
