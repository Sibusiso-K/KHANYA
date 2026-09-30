import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from webapi import app as api


KNOWN = {
    "de7135a96541a46dc0981a991cb954186c7cd669ea1c1b33914d1929ae9b1357":
        (0.5725, 0.8914, "reports/ACCURACY-REPORT.md"),
    "fb78727d4859947d3605ccf9374f8defbc40897e9cf1b1922a52c1832d387067":
        (0.4543, 0.7716, "reports/END-TO-END-LOCAL-DEMO-2026-09-30.md"),
}


@pytest.mark.parametrize("sha,expected", KNOWN.items())
def test_report_metrics_are_bound_to_the_loaded_checkpoint(monkeypatch, sha, expected):
    monkeypatch.setattr(api, "MODEL_SHA", sha)
    response = TestClient(api.app).get("/api/report")
    assert response.status_code == 200
    report = response.json()
    assert report["metrics"]["mean_iou"] == expected[0]
    assert report["metrics"]["pixel_accuracy"] == expected[1]
    assert report["report_source"] == expected[2]
    assert report["metrics_message"] is None
    active = [model for model in report["known_checkpoints"] if model["active"]]
    assert len(active) == 1
    assert active[0]["model_sha"] == sha


def test_unknown_checkpoint_has_no_reported_metrics(monkeypatch):
    monkeypatch.setattr(api, "MODEL_SHA", "0" * 64)
    report = TestClient(api.app).get("/api/report").json()
    assert report["metrics"] is None
    assert report["report_source"] is None
    assert report["metrics_message"] == "Unknown checkpoint; no metrics are available for this SHA-256."
    assert not any(model["active"] for model in report["known_checkpoints"])


def test_approval_contract_distinguishes_approved_and_other_checkpoints(monkeypatch):
    client = TestClient(api.app)
    for sha, approved in ((next(iter(KNOWN)), True), (list(KNOWN)[1], False), ("0" * 64, False)):
        monkeypatch.setattr(api, "MODEL_SHA", sha)
        health = client.get("/api/health").json()
        report = client.get("/api/report").json()
        assert health["model_approved"] is approved
        assert report["model_approved"] is approved
        assert health["approved_model_sha"] == report["approved_model_sha"]
