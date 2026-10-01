"""Fixed, independently audited evaluation evidence; never a deployment mechanism."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

CHECKPOINT_SHA = "42646cfafbeac5398386dba17f7ad3531ffcea572e6342cc4fcba42ed0b44b3b"
PROTOCOL_SHA = "8acb5998b06b67d7b542507dac4630dfea6fc422398d71050ee8e6894a263614"
EVALUATION_ID = "native-selected-test-20261001-v1"
CLASS_NAMES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]
COLORS = ["#8c96a1", "#f28136", "#d6ac25", "#119eae", "#9562d1"]
# These are exact downloaded evidence bytes, not a browser-controlled source.
ARTIFACTS = {
    "metrics": ("native_selected_test_metrics.json", "13bed0c61569fb840bdbb4039df8264655c14f3652d7ceb38dde8ed483c05692", "application/json"),
    "protocol": ("protocol.json", PROTOCOL_SHA, "application/json"),
    "report": ("evaluation_report.md", "0b28cfbfeb9ff92e5e9db1bdc48511fd48f592996bea2557166680bec80d77f8", "text/markdown"),
    "classes": ("test_per_class.csv", "39e910ccb0b6df8a98c5c1624a7b4f4701e5691498f5f466f15311981e622f36", "text/csv"),
    "sections": ("test_per_section.csv", "3ea387fdd8074491990e49b60a29436a04ea04d9f461b693e637227211cf4505", "text/csv"),
    "confusion": ("test_confusion.csv", "c4b8bd16d9e275010edcc839b0d5ce8d999fbf304c7fc6380b670f1a8ae459a1", "text/csv"),
}

class EvidenceUnavailable(ValueError):
    pass

def verified_artifact(directory: Path, artifact: str) -> tuple[Path, str]:
    if artifact not in ARTIFACTS:
        raise KeyError(artifact)
    name, expected, media_type = ARTIFACTS[artifact]
    path = directory / name
    try:
        # Disallow an escaped symlink even though its bytes would still need to match.
        path.resolve().relative_to(directory.resolve())
        content = path.read_bytes()
    except (OSError, ValueError) as exc:
        raise EvidenceUnavailable("Candidate evidence is unavailable.") from exc
    if len(content) > 2_000_000 or hashlib.sha256(content).hexdigest() != expected:
        raise EvidenceUnavailable("Candidate evidence failed its recorded SHA-256 check.")
    return path, media_type

def _close(a: float, b: float) -> bool:
    return math.isfinite(a) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)

def summary(directory: Path, active_sha: str) -> dict:
    path, _ = verified_artifact(directory, "metrics")
    protocol_path, _ = verified_artifact(directory, "protocol")
    try:
        measured = json.loads(path.read_text(encoding="utf-8"))
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        if not (
            measured["evaluation_id"] == protocol["evaluation_id"] == EVALUATION_ID
            and measured["checkpoint_sha256"] == protocol["checkpoint_sha256"] == CHECKPOINT_SHA
            and measured["protocol_sha256"] == PROTOCOL_SHA
            and measured["class_names"] == CLASS_NAMES
            and measured["class_codes"] == [0, 1, 3, 5, 7]
            and measured["n_test_sections"] == 12
            and measured["test_image_ids"] == protocol["test_image_ids"] == [f"test_{i:02d}" for i in range(1, 13)]
            and measured["candidate_epoch"] == protocol["candidate_epoch"] == 12
            and measured["confusion_orientation"] == "rows: ground truth, columns: prediction"
            and measured["training_performed"] is False
            and measured["test_used_for_selection"] is False
            and measured["automatic_deployment"] is False
        ):
            raise ValueError("Identity mismatch")
        matrix = measured["confusion_matrix"]
        if len(matrix) != 5 or any(len(row) != 5 or any(type(v) is not int or v < 0 for v in row) for row in matrix):
            raise ValueError("Invalid confusion matrix")
        rows = [sum(row) for row in matrix]
        columns = [sum(row[c] for row in matrix) for c in range(5)]
        classes = []
        for i, name in enumerate(CLASS_NAMES):
            tp, fp, fn = matrix[i][i], columns[i] - matrix[i][i], rows[i] - matrix[i][i]
            values = {"iou": tp / (tp + fp + fn), "recall": tp / (tp + fn), "precision": tp / (tp + fp)}
            for key, value in values.items():
                if not _close(measured[key + "_per_class"][i], value):
                    raise ValueError("Rates disagree with confusion matrix")
            if (measured["tp_per_class"][i], measured["fp_per_class"][i], measured["fn_per_class"][i]) != (tp, fp, fn):
                raise ValueError("Counts disagree with confusion matrix")
            classes.append({"name": name, "color": COLORS[i], **values, "support_pixels": rows[i], "false_positive_pixels": fp})
        mean_iou = sum(item["iou"] for item in classes) / 5
        foreground = sum(item["iou"] for item in classes[1:]) / 4
        accuracy = sum(matrix[i][i] for i in range(5)) / sum(rows)
        if not (_close(measured["mean_iou"], mean_iou) and _close(measured["pixel_accuracy"], accuracy) and _close(measured["foreground_macro_iou"], foreground)):
            raise ValueError("Aggregate rates disagree with counts")
    except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        raise EvidenceUnavailable("Candidate evidence failed its identity or metric consistency check.") from exc
    return {
        "evaluation_id": EVALUATION_ID, "model_sha": CHECKPOINT_SHA,
        "active_model_sha": active_sha, "candidate_is_active": CHECKPOINT_SHA == active_sha,
        "deployment_status": "active-checkpoint" if CHECKPOINT_SHA == active_sha else "candidate-not-deployed",
        "verified_evidence": True, "protocol_sha": PROTOCOL_SHA,
        "completed_at": measured["finished_at_utc"], "candidate_epoch": 12,
        "metrics": {"mean_iou": mean_iou, "foreground_macro_iou": foreground, "pixel_accuracy": accuracy, "n_test_sections": 12, "classes": classes},
        "method": measured["method"], "selection_rule": measured["selection_rule"],
        "limitations": [
            measured["historical_test_caveat"],
            "Magnetite precision is 25.5% despite 89.3% recall: 2,140,808 false-positive pixels. Most magnetite predictions are incorrect on this set.",
            "Compared with the historical approved report, pyrrhotite IoU (0.818 vs 0.870), pentlandite IoU (0.446 vs 0.547), and pixel accuracy (0.855 vs 0.891) are lower. Older reports are not bound to this run's exact source and mask hashes; this is not a controlled uplift comparison.",
            "One seed and twelve whole images; images are not verified independent specimens or localities. No prospective ore, plant or recovery validation.",
            "Evaluation does not approve or deploy this checkpoint. Active inference, assistant scores and simulator gates remain separate.",
        ],
        "downloads": [{"key": key, "filename": value[0], "sha256": value[1], "url": f"/api/reports/native-candidate/download/{key}"} for key, value in ARTIFACTS.items()],
    }
