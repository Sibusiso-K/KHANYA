"""Uploads fail visibly before expensive inference begins."""
import io

import pytest
from PIL import Image

from src.input_checks import load_image, unavailable_reason


def test_corrupt_image_is_rejected():
    with pytest.raises(ValueError, match="could not be decoded"):
        load_image(b"not an image")


def test_decoded_image_survives_closed_input_stream():
    buf = io.BytesIO()
    Image.new("RGB", (12, 8), (5, 10, 20)).save(buf, format="PNG")
    image = load_image(buf.getvalue())
    assert image.size == (12, 8)
    assert image.getpixel((0, 0)) == (5, 10, 20)


def test_unvalidated_subset_is_not_given_s2_band(tmp_path):
    assert "no validated" in unavailable_reason("S1", tmp_path / "best.pt")


def test_missing_checkpoint_is_reported_before_upload(tmp_path):
    assert "checkpoint is missing" in unavailable_reason("S2", tmp_path / "best.pt")


def test_application_starts_with_visible_refusal_without_checkpoint(monkeypatch, tmp_path):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from src.segmentation import config

    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setenv("KHANYA_SUBSET", "S2")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard/app.py"))
    app.run(timeout=20)
    assert not app.exception
    frames = app.get("iframe")
    assert frames
    assert "checkpoint is missing" in frames[0].proto.srcdoc

