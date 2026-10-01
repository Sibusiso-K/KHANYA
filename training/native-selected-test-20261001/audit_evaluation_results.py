"""Recompute the completed evaluation's small reports without dataset or weights."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
protocol_bytes = (HERE / "protocol.json").read_bytes()
protocol = json.loads(protocol_bytes)
summary = json.loads((RESULTS / "native_selected_test_metrics.json").read_text(encoding="utf-8"))
assert (RESULTS / "protocol.json").read_bytes() == protocol_bytes
assert summary["protocol_sha256"] == hashlib.sha256(protocol_bytes).hexdigest()
for key in ("checkpoint_sha256", "source_bundle_sha256", "candidate_manifest_sha256", "dataset_archive_sha256", "dataset_archive_bytes", "class_names", "class_codes", "test_image_ids", "source_file_sha256", "candidate_epoch", "candidate_run_id", "evaluation_id"):
    assert summary[key] == protocol[key], key
assert summary["n_test_sections"] == 12
assert summary["checkpoint_bytes"] > 0
assert summary["training_performed"] is False and summary["automatic_deployment"] is False
assert summary["test_used_for_selection"] is False
assert summary["confusion_orientation"] == "rows: ground truth, columns: prediction"
assert summary["runtime"]["torch"] == protocol["expected_runtime"]["torch"]
assert summary["runtime"]["torchvision"] == protocol["expected_runtime"]["torchvision"]
assert list(summary["per_section"]) == protocol["test_image_ids"]
assert list(summary["test_file_sha256"]) == protocol["test_image_ids"]


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def close(actual, expected):
    assert (actual is None and expected is None) or (
        actual is not None and expected is not None and math.isfinite(actual)
        and math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0)
    ), (actual, expected)


def verify(item):
    matrix = item["confusion_matrix"]
    assert len(matrix) == 5 and all(len(row) == 5 for row in matrix)
    assert all(type(value) is int and value >= 0 for row in matrix for value in row)
    tp = [matrix[c][c] for c in range(5)]
    truth = [sum(row) for row in matrix]
    prediction = [sum(matrix[r][c] for r in range(5)) for c in range(5)]
    fp = [prediction[c] - tp[c] for c in range(5)]
    fn = [truth[c] - tp[c] for c in range(5)]
    for key, expected in (("tp_per_class", tp), ("fp_per_class", fp), ("fn_per_class", fn), ("ground_truth_pixels_per_class", truth), ("predicted_pixels_per_class", prediction)):
        assert item[key] == expected, key
    ious = [ratio(t, t + p + n) for t, p, n in zip(tp, fp, fn)]
    recalls = [ratio(t, t + n) for t, n in zip(tp, fn)]
    precisions = [ratio(t, t + p) for t, p in zip(tp, fp)]
    for key, expected in (("iou_per_class", ious), ("recall_per_class", recalls), ("precision_per_class", precisions)):
        for actual, value in zip(item[key], expected):
            close(actual, value)
    valid_ious = [v for v in ious if v is not None]
    foreground_ious = [v for v in ious[1:] if v is not None]
    close(item["mean_iou"], sum(valid_ious) / len(valid_ious))
    close(item["foreground_macro_iou"], sum(foreground_ious) / len(foreground_ious) if foreground_ious else None)
    close(item["pixel_accuracy"], sum(tp) / sum(truth))
    assert item["evaluated_class_count"] == len(valid_ious)
    assert item["evaluated_foreground_class_count"] == len(foreground_ious)
    return matrix


pooled = verify(summary)
sum_matrix = [[0] * 5 for _ in range(5)]
for stem, item in summary["per_section"].items():
    matrix = verify(item)
    assert sum(sum(row) for row in matrix) == item["image_width"] * item["image_height"]
    for r in range(5):
        for c in range(5):
            sum_matrix[r][c] += matrix[r][c]
    for hash_name in ("image_sha256", "mask_sha256"):
        assert len(summary["test_file_sha256"][stem][hash_name]) == 64
assert sum_matrix == pooled
for name in protocol["exported_outputs"]:
    assert (RESULTS / name).is_file(), name
result = {
    "audit_passed": True,
    "confusion_metrics_recomputed": True,
    "twelve_section_matrices_sum_to_pooled": True,
    "all_section_pixels_counted": True,
    "provenance_matches_predeclared_protocol": True,
    "five_class_mean_iou": summary["mean_iou"],
    "foreground_macro_iou": summary["foreground_macro_iou"],
    "pixel_accuracy": summary["pixel_accuracy"],
    "iou_per_class": summary["iou_per_class"],
    "recall_per_class": summary["recall_per_class"],
    "results_file_sha256": hashlib.sha256((RESULTS / "native_selected_test_metrics.json").read_bytes()).hexdigest(),
    "automatic_deployment": False,
    "note": "Fixed historical regression set; single-seed result. No training or checkpoint bytes used in this offline audit.",
}
(HERE / "result_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
