"""The quick workbench result is built from six real model fields."""
import importlib
import sys
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi")

import numpy as np
from PIL import Image

torch = pytest.importorskip("torch")
api = importlib.import_module("webapi.app")

def test_synthetic_section_has_six_nonoverlapping_fields_and_visible_coverage():
    from src.segmentation.patches import field_boxes, field_coverage
    count, coverage = field_coverage(1600, 1100)
    boxes = field_boxes(1600, 1100)
    assert count == len(boxes) == 6
    assert coverage == pytest.approx(6 * 512 * 512 / (1600 * 1100))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]

def test_quick_inference_uses_six_field_predictor_and_records_measured_scope(tmp_path, monkeypatch):
    ckpt = tmp_path / "best.pt"; ckpt.write_bytes(b"checkpoint")
    image_path = tmp_path / "section.png"
    Image.new("RGB", (1600, 1100), (190, 130, 80)).save(image_path)
    monkeypatch.setattr(api, "CKPT", ckpt)
    monkeypatch.setattr(api, "CKPT_STAMP", ckpt.stat().st_mtime_ns)
    monkeypatch.setattr(api, "MODEL_SHA", "test-sha")
    monkeypatch.setattr(api, "STORE", tmp_path / "store")
    api.STORE.mkdir()
    monkeypatch.setattr(api, "samples", {"sample": image_path})
    monkeypatch.setattr(api, "model", object())
    monkeypatch.setattr(api, "jobs", {"job": {"id": "job", "status": "queued"}})
    calls = []
    def predict(model, image, device, progress_callback=None):
        calls.append((model, image.size, device))
        progress_callback(1,6,np.zeros((1100,1600),dtype=np.int64),(0,0,512,512),.91)
        assert api.jobs["job"]["progress"]["completed"] == 1
        labels = np.zeros((1026, 1540), dtype=np.int64)
        mosaic = Image.new("RGB", (1540, 1026), (190, 130, 80))
        return labels, .91, mosaic, [(0, 0, 512, 512)] * 6
    from src.segmentation import patches
    monkeypatch.setattr(patches, "multi_field_predict", predict)
    monkeypatch.setattr(patches, "field_coverage", lambda w, h: (6, 6 * 512 * 512 / (w * h)))
    monkeypatch.setattr(patches, "sliding_window_predict", lambda *a, **k: pytest.fail("quick mode must not use whole-section tiling"))
    from src import modal, advisor
    monkeypatch.setattr(modal, "analyse", lambda *a, **k: SimpleNamespace(liberation=None, phase_fractions={name: 0.0 for name in api.CLASSES}))
    monkeypatch.setattr(advisor, "advise", lambda *a, **k: SimpleNamespace(action="Continue at current setpoint", reason="Measured advisory"))
    monkeypatch.setattr(api, "verified_hashes", {})
    from webapi import safety
    monkeypatch.setattr(safety, "check_input_colour", lambda image: None)
    monkeypatch.setattr(safety, "input_evidence", lambda raw: {"verified": True, "verified_sample": "test_11"})
    api.run_inference("job", "sample", "field")
    assert api.jobs["job"]["status"] == "complete", (
        f"Quick inference failed: {api.jobs['job'].get('error', 'no error details returned')}"
    )
    result = api.jobs["job"]["result"]
    progress = api.jobs["job"]["progress"]
    assert progress["stage"] == "measuring"
    assert progress["evidence"]["analysed_pixels"] == 512 * 512
    assert progress["evidence"]["phases"][0]["area_pct"] == 100
    assert progress["evidence"]["unknown_pixels"] == 1600 * 1100 - 512 * 512
    assert len(calls) == 1 and calls[0][1:] == ((1600, 1100), "cpu")
    assert result["field_count"] == 6
    assert result["field_coverage"] == pytest.approx(6 * 512 * 512 / (1600 * 1100))
    assert "6 × 512 px fields" in result["scope"]
    assert "89.4% area coverage" in result["scope"]
    assert result["raw_url"].endswith("layer=raw&result_id=" + result["result_id"])
