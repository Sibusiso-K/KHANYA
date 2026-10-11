from __future__ import annotations

import hashlib
import importlib
import io
import json

import pytest
pytest.importorskip("fastapi")
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

api = importlib.import_module("webapi.app")
from src import modal
from webapi.grain_evidence import write_grain_evidence

NAMES = ["background", "chalcopyrite", "magnetite", "pyrrhotite", "pentlandite"]


def synthetic_labels():
    labels = np.zeros((120, 120), dtype=np.int64)
    labels[10:40, 10:40] = 1
    labels[60:110, 60:110] = 3
    labels[80:90, 80:90] = 4
    return labels


@pytest.fixture
def grain_api(tmp_path, monkeypatch):
    source = tmp_path / "section.png"
    Image.new("RGB", (120, 120), (180, 120, 70)).save(source)
    store = tmp_path / "store"
    store.mkdir()
    monkeypatch.setattr(api, "STORE", store)
    monkeypatch.setattr(api, "samples", {"sample-one": source})
    monkeypatch.setattr(api, "results", {})
    labels = synthetic_labels()
    measured = modal.analyse(labels, NAMES, refine=True)
    result_id = "grain-result-1"
    image_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    result = {"result_id": result_id, "id": "sample-one", "model_sha": api.MODEL_SHA,
              "image_sha": image_sha, "contract": 1}
    directory = store / f"sample-one-{result_id}"
    directory.mkdir()
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    report = write_grain_evidence(labels, NAMES, measured.phase_fractions, directory)
    api.results[result_id] = result
    return TestClient(api.app), result_id, labels, measured, report, source


def test_api_grain_count_matches_advisor_particle_count(grain_api):
    client, result_id, _, measured, report, _ = grain_api
    response = client.get(f"/api/results/{result_id}/grains")
    assert response.status_code == 200
    body = response.json()
    assert body["n_grains"] == measured.n_particles
    assert body["n_grains"] == len(body["grains"])
    assert body["n_payload_grains"] == measured.n_payload_particles
    assert body["weight_percent"] == report["weight_percent"]
    assert {"association", "liberation_by_size", "microns_per_pixel"} <= body.keys()


def test_grain_id_png_round_trips_every_integer_exactly(grain_api):
    client, result_id, labels, _, _, _ = grain_api
    response = client.get(f"/api/results/{result_id}/grain-ids.png")
    assert response.status_code == 200
    rgb = np.asarray(Image.open(io.BytesIO(response.content)).convert("RGB"), dtype=np.uint32)
    decoded = rgb[..., 0] + 256 * rgb[..., 1] + 65536 * rgb[..., 2]
    from src.grains import grain_report
    expected = grain_report(labels, NAMES).grain_map.astype(np.uint32)
    np.testing.assert_array_equal(decoded, expected)


def test_unknown_result_id_returns_404_for_both_grain_endpoints(grain_api):
    client, _, *_ = grain_api
    assert client.get("/api/results/missing/grains").status_code == 404
    assert client.get("/api/results/missing/grain-ids.png").status_code == 404


def test_stale_source_image_returns_404_for_both_grain_endpoints(grain_api):
    client, result_id, _, _, _, source = grain_api
    source.write_bytes(b"source changed after inference")
    assert client.get(f"/api/results/{result_id}/grains").status_code == 404
    assert client.get(f"/api/results/{result_id}/grain-ids.png").status_code == 404
