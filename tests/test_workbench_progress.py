"""Live previews are real completed predictions, with unknown pixels excluded."""
from __future__ import annotations

import importlib
import io
import json
import uuid

import numpy as np
from PIL import Image
import pytest

pytest.importorskip("fastapi")
from fastapi import HTTPException
from fastapi.testclient import TestClient
from webapi.progress import InferenceEvidence, read_preview, MAX_PREVIEW_BYTES, MAX_PREVIEW_SIDE

api = importlib.import_module("webapi.app")
NAMES = api.CLASSES
COLORS = api.COLORS


def test_unanalysed_background_and_foreground_never_enter_phase_denominator(tmp_path):
    evidence = InferenceEvidence(tmp_path, "job", (10, 8), NAMES, COLORS, "field")
    labels = np.full((8, 10), 4, dtype=np.int64)
    labels[1:3, 1:4] = [[0, 1, 1], [0, 1, 0]]
    snapshot = evidence.publish(1, 2, labels, (1, 1, 4, 3), .73)
    assert snapshot["analysed_pixels"] == 6
    assert snapshot["unknown_pixels"] == 74
    assert snapshot["coverage_fraction"] == pytest.approx(6 / 80)
    assert [p["pixels"] for p in snapshot["phases"]] == [3, 3, 0, 0, 0]
    assert sum(p["area_pct"] for p in snapshot["phases"]) == pytest.approx(100)
    assert snapshot["phases"][1]["area_pct"] == 50
    assert snapshot["preview_url"] == "/api/jobs/job/preview?revision=1"
    assert snapshot["provisional"] is True
    data, revision = read_preview(tmp_path, "job")
    pixels = np.asarray(Image.open(io.BytesIO(data)))
    assert revision == 1
    assert np.count_nonzero(pixels[..., 3]) == 6
    assert not pixels[0, 0].any()
    assert pixels[1, 2].tolist() == [242, 129, 54, 190]


def test_overlapping_tiles_count_union_once_and_negative_or_unknown_ids_are_excluded(tmp_path):
    evidence = InferenceEvidence(tmp_path, "job", (8, 6), NAMES, COLORS, "full")
    labels = np.full((6, 8), -1, dtype=np.int32)
    labels[:4, :4] = 1
    first = evidence.publish(1, 2, labels, (0, 0, 4, 4), .8)
    labels[2:6, 2:6] = 3
    labels[2, 2] = 255
    second = evidence.publish(2, 2, labels, (2, 2, 6, 6), .9)
    assert first["analysed_pixels"] == 16
    assert second["analysed_pixels"] == 27  # 16 + 16 - 4 overlap - 1 invalid
    assert second["invalid_pixels"] == 1
    assert second["unknown_pixels"] == 20
    assert [p["pixels"] for p in second["phases"]] == [0, 12, 0, 15, 0]
    assert "final overlap blending" in second["aggregation"]
    assert second["last_tile_confidence"] == .9
    assert first["completed_boxes"] == [[0, 0, 4, 4]]  # old polling snapshots immutable
    assert second["completed_boxes"] == [[0, 0, 4, 4], [2, 2, 6, 6]]
    assert read_preview(tmp_path, "job")[1] == 2
    assert {p.name for p in (tmp_path / "progress" / "job").iterdir()} == {"latest.png", "latest.json"}
    assert len(json.dumps(second)) < 4096


def test_preview_resizes_display_only_and_bounds_bytes(tmp_path):
    evidence = InferenceEvidence(tmp_path, "job", (1600, 1100), NAMES, COLORS, "field")
    labels = np.zeros((1100, 1600), dtype=np.int64)
    labels[100:612, 100:612] = 3
    snapshot = evidence.publish(1, 1, labels, (100, 100, 612, 612), .81)
    data, _ = read_preview(tmp_path, "job")
    assert max(snapshot["preview_size"]) == MAX_PREVIEW_SIDE
    assert len(data) < MAX_PREVIEW_BYTES
    assert snapshot["analysed_pixels"] == 512 * 512
    assert snapshot["phases"][3]["area_pct"] == 100


@pytest.mark.parametrize("job_id", ["../job", "/absolute", "a" * 65, "job/name"])
def test_job_paths_cannot_escape_current_workspace(tmp_path, job_id):
    with pytest.raises(ValueError, match="identifier"):
        InferenceEvidence(tmp_path, job_id, (8, 6), NAMES, COLORS, "field")


@pytest.mark.parametrize("completed,total,box", [(0, 1, (0, 0, 4, 4)), (1, 0, (0, 0, 4, 4)),
                                                  (1, 1, (-1, 0, 4, 4)), (1, 1, (0, 0, 9, 4))])
def test_invalid_callbacks_do_not_publish_pixels(tmp_path, completed, total, box):
    evidence = InferenceEvidence(tmp_path, "job", (8, 6), NAMES, COLORS, "field")
    with pytest.raises(ValueError):
        evidence.publish(completed, total, np.zeros((6, 8), dtype=np.int64), box, .7)
    assert not (tmp_path / "progress" / "job" / "latest.png").exists()


def test_real_multi_field_callback_has_unknown_gaps_even_when_source_array_is_zero(tmp_path):
    torch = pytest.importorskip("torch")
    from src.segmentation.patches import multi_field_predict

    class PhaseModel:
        def __call__(self, tile):
            logits = torch.zeros((1, len(NAMES), tile.shape[-2], tile.shape[-1]))
            logits[:, 1] = 4
            return {"out": logits}

    image = Image.new("RGB", (1200, 512), (180, 120, 70))
    evidence = InferenceEvidence(tmp_path, "real", image.size, NAMES, COLORS, "field")
    snapshots = []
    def callback(completed, total, labels, box, confidence):
        snapshots.append(evidence.publish(completed, total, labels, box, confidence))
    multi_field_predict(PhaseModel(), image, "cpu", progress_callback=callback)
    assert len(snapshots) == 2
    assert snapshots[0]["analysed_pixels"] == 512 * 512
    assert snapshots[1]["analysed_pixels"] == 2 * 512 * 512
    assert snapshots[1]["unknown_pixels"] == 1200 * 512 - 2 * 512 * 512
    assert snapshots[1]["phases"][0]["pixels"] == 0
    assert snapshots[1]["phases"][1]["area_pct"] == 100


def test_real_sliding_window_callbacks_count_unique_source_pixels_not_overlapping_tile_area(tmp_path):
    torch = pytest.importorskip("torch")
    from src.segmentation.patches import sliding_window_predict

    class PhaseModel:
        def __call__(self, tile):
            logits = torch.zeros((1, len(NAMES), tile.shape[-2], tile.shape[-1]))
            logits[:, 3] = 5
            return {"out": logits}

    image = Image.new("RGB", (96, 96), (180, 120, 70))
    evidence = InferenceEvidence(tmp_path, "tiled", image.size, NAMES, COLORS, "full")
    snapshots = []
    def callback(completed, total, labels, box, confidence):
        snapshots.append(evidence.publish(completed, total, labels, box, confidence))
    final, _ = sliding_window_predict(PhaseModel(), image, "cpu", patch=64, overlap=16,
                                      progress_callback=callback)
    assert len(snapshots) == 4
    assert snapshots[0]["analysed_pixels"] == 64 * 64
    assert snapshots[0]["unknown_pixels"] == 96 * 96 - 64 * 64
    assert snapshots[-1]["analysed_pixels"] == 96 * 96  # not four 64x64 tiles
    assert snapshots[-1]["coverage_fraction"] == 1
    assert snapshots[-1]["unknown_pixels"] == 0
    assert snapshots[-1]["phases"][3]["pixels"] == np.count_nonzero(final == 3)


def test_preview_byte_limit_fails_before_publishing_file(tmp_path, monkeypatch):
    from webapi import progress
    monkeypatch.setattr(progress, "MAX_PREVIEW_BYTES", 10)
    evidence = InferenceEvidence(tmp_path, "job", (8, 6), NAMES, COLORS, "field")
    with pytest.raises(ValueError, match="byte limit"):
        evidence.publish(1, 1, np.ones((6, 8), dtype=np.int64), (0, 0, 4, 4), .7)
    assert not (tmp_path / "progress" / "job" / "latest.png").exists()


@pytest.fixture
def public_preview(tmp_path, monkeypatch):
    monkeypatch.setenv("REEFPRINT_DEPLOYMENT", "public")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_fixture")
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(api.cloud, "tenants", {})
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    def verify(token):
        if token not in (a, b):
            raise HTTPException(401, "Invalid session")
        return {"id": token, "token": token}
    monkeypatch.setattr(api.cloud, "verify", verify)
    context = api.cloud.identity.set({"id": a, "token": a})
    try:
        api.workspace_jobs()["private-job"] = {"id": "private-job", "status": "running"}
        api.workspace_jobs()["empty-job"] = {"id": "empty-job", "status": "queued"}
        evidence = InferenceEvidence(api.workspace_store(), "private-job", (8, 6), NAMES, COLORS, "field")
        evidence.publish(1, 1, np.ones((6, 8), dtype=np.int64), (0, 0, 4, 4), .81)
    finally:
        api.cloud.identity.reset(context)
    return TestClient(api.app), a, b


def test_progress_png_requires_verified_user_and_same_tenant(public_preview):
    client, a, b = public_preview
    url = "/api/jobs/private-job/preview?revision=1"
    assert client.get(url).status_code == 401
    assert client.get(url, headers={"Authorization": "Bearer forged"}).status_code == 401
    assert client.get(url, headers={"Authorization": "Bearer " + b}).status_code == 404
    response = client.get(url, headers={"Authorization": "Bearer " + a})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-reefprint-preview-revision"] == "1"
    assert response.headers["x-reefprint-provisional"] == "true"
    assert client.get("/api/jobs/empty-job/preview", headers={"Authorization": "Bearer " + a}).status_code == 404
    assert api.cloud.identity.get() is None
