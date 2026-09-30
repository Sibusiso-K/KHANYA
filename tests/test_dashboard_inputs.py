"""Uploads fail visibly before expensive inference begins."""
import io

import pytest
from PIL import Image

from dashboard.inputs import load_image, unavailable_reason


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


# Input eligibility (pre-production finding 1). Synthetic images only: CI has no data.
import json  # noqa: E402

import numpy as np  # noqa: E402

from dashboard.inputs import CHROMA_FLOOR, check_colour_cast, colour_cast_reason, validated_sample  # noqa: E402
from src.segmentation import config  # noqa: E402


def _image(rgb):
    return Image.fromarray(np.full((64, 64, 3), rgb, dtype=np.uint8))


def test_warm_micrograph_like_image_is_eligible():
    assert colour_cast_reason(_image((190, 175, 160))) is None


def test_greyscale_image_is_refused_before_inference():
    with pytest.raises(ValueError, match="no colour"):
        check_colour_cast(_image((150, 150, 150)).convert("L"))


def test_cool_cast_image_is_refused():
    # the text screenshot's balance: red below green, blue above green
    assert "colour balance" in colour_cast_reason(_image((128, 151, 158)))


def test_gate_is_the_rule_the_committed_evidence_measured():
    evidence = json.loads((config.ROOT / "reports" / "input_eligibility.json").read_text())
    assert evidence["rule"]["chroma_floor"] == CHROMA_FLOOR
    assert evidence["rule"]["fitted_thresholds"] == 0
    for name, result in evidence["sets"].items():
        if name.startswith("S2"):
            assert result["eligible"] == result["n"], name
            assert result["eligible_after_lighting_shift"] == result["n"], name
    assert not any(h["eligible"] for h in evidence["hostile"].values())


def test_dashboard_gate_matches_the_measurement_script():
    from src.input_eligibility_check import eligible, features

    for rgb in [(190, 175, 160), (150, 150, 150), (128, 151, 158), (120, 121, 119),
                (200, 150, 170), (90, 100, 60), (180, 170, 171), (60, 58, 50)]:
        array = np.asarray(_image(rgb), dtype=np.float32)
        assert eligible(features(array)) == (colour_cast_reason(_image(rgb)) is None), rgb


def test_only_the_validated_held_out_sections_may_drive_the_simulator():
    manifest = json.loads((config.ROOT / "dashboard" / "validated_samples.json").read_text())
    assert sorted(manifest["sha256"]) == [f"test_{i:02d}" for i in range(1, 13)]
    assert all(len(d) == 64 and int(d, 16) >= 0 for d in manifest["sha256"].values())
    assert validated_sample(b"any other upload") is None


def test_a_validated_file_is_recognised_and_a_converted_copy_is_not():
    import io

    path = config.ROOT / "data" / "raw" / "lumenstone" / "S2_v2" / "imgs" / "test" / "test_11.jpg"
    if not path.exists():
        pytest.skip("held-out data not present (CI)")
    original = path.read_bytes()
    assert validated_sample(original) == "test_11"
    buf = io.BytesIO()
    Image.open(io.BytesIO(original)).save(buf, format="PNG")
    assert validated_sample(buf.getvalue()) is None
