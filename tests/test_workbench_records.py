import pytest
pytest.importorskip("fastapi")
import importlib
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

api = importlib.import_module("webapi.app")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "STORE", tmp_path)
    monkeypatch.setattr(api, "samples", {"sample-one": tmp_path / "sample.jpg"})
    return TestClient(api.app)


def test_record_roundtrip_persists_to_disk(client, tmp_path):
    url = "/api/samples/sample-one/record"
    assert client.get(url).json() == {
        "sample_id": "sample-one", "version": 0, "updated_at": None, "record": {}}
    record = {"sample_label": "Core A", "latitude": -26.2, "longitude": 28.0,
              "depth": 0, "notes": "First field", "assays": [
                  {"element": "Ni", "value": 0.5, "unit": "%"}], "assayFile": "assays.csv"}
    response = client.put(url, json={"expected_version": 0, "record": record})
    assert response.status_code == 200
    saved = response.json()
    assert saved["record"] == record
    assert saved["version"] == 1
    assert saved["updated_at"].endswith("+00:00")
    assert json.loads((tmp_path / "records/sample-one.json").read_text()) == saved
    assert client.get(url).json() == saved
    replacement = client.put(url, json={"expected_version": 1, "record": {"notes": "Updated"}})
    assert replacement.json()["version"] == 2
    assert replacement.json()["record"] == {"notes": "Updated"}
    assert not list((tmp_path / "records").glob("*.tmp"))


def test_stale_write_preserves_saved_record(client):
    url = "/api/samples/sample-one/record"
    first = client.put(url, json={"expected_version": 0, "record": {"notes": "First"}}).json()
    conflict = client.put(url, json={"expected_version": 0, "record": {"notes": "Stale"}})
    assert conflict.status_code == 409
    assert "Reload" in conflict.json()["detail"]
    assert client.get(url).json() == first


def test_unknown_sample(client, tmp_path):
    assert client.get("/api/samples/missing/record").status_code == 404
    assert client.put("/api/samples/missing/record", json={"expected_version": 0, "record": {}}).status_code == 404
    assert not (tmp_path / "records").exists()


@pytest.mark.parametrize("record", [
    {"latitude": 90.1}, {"longitude": -180.1}, {"depth": -1},
    {"latitude": "25"}, {"notes": "x" * 10001}, {"sample_label": "x" * 201},
    {"assayFile": "x" * 256}, {"unknown": True},
    {"assays": [{"element": "Ni", "value": -1, "unit": "%"}]},
    {"assays": [{"element": "Ni", "value": 1, "unit": "%", "extra": 1}]},
    {"assays": [{"element": "x" * 31, "value": 1, "unit": "%"}]},
    {"assays": [{"element": "Ni", "value": 1, "unit": "x" * 31}]},
    {"assays": [{"element": "Ni", "value": 1, "unit": "%"}] * 201},
])
def test_invalid_records_rejected(client, record):
    assert client.put("/api/samples/sample-one/record", json={"expected_version": 0, "record": record}).status_code == 422


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_values_rejected(value):
    for field in ("latitude", "longitude", "depth"):
        with pytest.raises(ValidationError):
            api.SampleRecord.model_validate({field: value})
    with pytest.raises(ValidationError):
        api.SampleRecord.model_validate({"assays": [{"element": "Ni", "value": value, "unit": "%"}]})


@pytest.mark.parametrize("body", [
    {"expected_version": True, "record": {}},
    {"expected_version": -1, "record": {}},
    {"expected_version": 0, "record": {}, "extra": 1},
])
def test_invalid_envelopes_rejected(client, body):
    assert client.put("/api/samples/sample-one/record", json=body).status_code == 422


def test_atomic_failure_keeps_previous_record(client, monkeypatch):
    url = "/api/samples/sample-one/record"
    first = client.put(url, json={"expected_version": 0, "record": {"notes": "First"}}).json()
    def fail_replace(*args):
        raise OSError("Disk failure")
    monkeypatch.setattr(api.os, "replace", fail_replace)
    with pytest.raises(OSError):
        client.put(url, json={"expected_version": 1, "record": {"notes": "Second"}})
    assert client.get(url).json() == first


@pytest.mark.parametrize("identifier", ["../x", "..%2Fx", "test_11.json", "unknown"])
def test_record_paths_reject_crafted_and_unknown_identifiers(client, tmp_path, identifier):
    api.samples["test_11.json"] = tmp_path / "sample.json"
    encoded = identifier.replace("%", "%25").replace("/", "%2F")
    base = f"/api/samples/{encoded}/record"
    payload = {"expected_version": 0, "record": {"notes": "must not escape"}}
    get_response = client.get(base)
    put_response = client.put(base, json=payload)
    assert get_response.status_code in (400, 404)
    assert put_response.status_code in (400, 404, 405)
    assert not (tmp_path.parent / "x.json").exists()
    assert not (tmp_path / "records" / "test_11.json.json").exists()
