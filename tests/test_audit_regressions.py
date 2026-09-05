"""Regression cases found during the 2026-09-05 project audit."""
import numpy as np
import pytest

from src import advisor, conformal, modal


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_liberation_cannot_become_a_confident_action(value):
    result = modal.ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0},
                               0.8, value, 2, 100)
    rec = advisor.advise(result, 0.99)
    assert rec.action == "No recommendation - invalid measurement"
    assert "liberation" in rec.reason


def test_dropped_payload_is_unmeasured_even_when_gangue_survives():
    labels = np.zeros((30, 30), dtype=np.int32)
    labels[2:12, 2:12] = 2
    labels[20:22, 20:22] = 1
    liberation, count = modal.liberation_index(labels, labels == 1)
    assert count == 1
    assert liberation is None
    result = modal.analyse(labels, ["background", "chalcopyrite", "pyrite"])
    assert "not measurable" in advisor.advise(result, 0.99).action


@pytest.mark.parametrize("alpha", [0, 1, -0.1, float("nan")])
def test_invalid_conformal_level_is_rejected(alpha):
    with pytest.raises(ValueError, match="alpha"):
        conformal.quantile_halfwidth([0.1, 0.2], alpha)


@pytest.mark.parametrize("residual", [-1, float("nan"), float("inf")])
def test_invalid_conformal_residual_is_rejected(residual):
    with pytest.raises(ValueError, match="residuals"):
        conformal.quantile_halfwidth([0.1, residual], 0.5)


def test_reagent_intervention_is_not_presented_as_within_specification():
    style, state = advisor.verdict_state("Adjust reagent dosage - depress reject phase")
    assert style == "grind"
    assert "intervention" in state


@pytest.mark.parametrize("labels", [np.array([[99]]), np.array([[-1]]), np.array([[1.5]])])
def test_invalid_class_ids_cannot_silently_change_ore_fractions(labels):
    with pytest.raises(ValueError):
        modal.analyse(labels, ["background", "chalcopyrite"])


def test_empty_calibration_report_fails_with_actionable_reason(monkeypatch, tmp_path, capsys):
    import json
    from src.segmentation import config

    (tmp_path / "empty.json").write_text(json.dumps({"rows": []}), encoding="utf-8")
    monkeypatch.setattr(config, "REPORT_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["conformal", "--run", "empty.json"])
    with pytest.raises(SystemExit) as exc:
        conformal.main()
    assert exc.value.code == 2
    assert "at least two measured" in capsys.readouterr().err


def test_checkpoint_architecture_builds_without_downloads(monkeypatch):
    """Exercise torchvision itself with its download function blocked."""
    import torch
    import torchvision.models._api as weights_api
    from src.segmentation.model import build_model

    def forbidden_download(*args, **kwargs):
        pytest.fail("offline model construction attempted to download weights")

    monkeypatch.setattr(weights_api, "load_state_dict_from_url", forbidden_download)
    model = build_model(num_classes=5, pretrained=False)
    assert isinstance(model.classifier[4], torch.nn.Conv2d)
    assert model.classifier[4].out_channels == 5
    assert model.aux_classifier[4].out_channels == 5
