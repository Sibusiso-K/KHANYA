"""Contracts for the offline Stitch renderer.

These test the two failure modes a visual inspection could easily miss: a
missing vendored asset must say how to repair the build, and only a genuinely
marginal verdict may offer the two equally weighted candidate actions.
"""
import ast
from pathlib import Path

import pytest

from dashboard import render
from src.advisor import Recommendation


def test_dashboard_app_embeds_the_stitch_renderer():
    """The old CSS-token approximation must not quietly become the UI again."""
    app_source = (
        Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    ).read_text(encoding="utf-8")

    assert "html = render.render(" in app_source
    assert "render.render_landing(" in app_source
    assert "st.components.v1.html(" in app_source
    assert "KHANYA_CSS" not in app_source


def test_dashboard_can_show_stitch_before_the_model_stack_is_loaded():
    """A missing checkpoint must not prevent the landing dashboard booting."""
    app_path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    tree = ast.parse(app_path.read_text(encoding="utf-8"))
    top_level_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "torch" not in top_level_imports
    assert "modal" not in top_level_imports
    assert "model" not in top_level_imports
    assert "patches" not in top_level_imports


def test_pre_upload_state_is_stitch_rendered_without_fabricated_claims():
    html = render.render_landing()

    assert "Plants learn what is in their ore days too late." in html
    assert "refuses to advise" in html
    assert "in seconds" not in html   # not true while the lighting check doubles the live pass
    assert "REEFPRINT :: KHANYA" in html
    assert "No network required" in html
    assert "Dr. K. Vance" not in html
    assert "ISO/IEC 17025" not in html
    assert "DISPATCH" not in html


def test_missing_static_asset_names_the_repair_step():
    with pytest.raises(FileNotFoundError, match="compile step"):
        render._read_text("not-a-real-static-asset.css")


def test_startup_refusal_is_visible_and_escapes_untrusted_text():
    html = render.render_landing("Missing model <script>alert(1)</script>")
    assert "Analysis unavailable" in html
    assert "No recommendation has been issued" in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


@pytest.mark.parametrize("liberation, expected", [
    (0.95, "within specification"),
    (0.5, "marginal, verify before acting"),
    (None, "measurement declined"),
])
def test_full_result_renders_the_actual_advisor_state(liberation, expected):
    import re
    import numpy as np
    from PIL import Image
    from src.advisor import advise
    from src.modal import ModalResult

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0},
                         0.8, liberation, 1, 64, n_payload_particles=12)
    recommendation = advise(result, 0.95)
    html = render.render(Image.new("RGB", (8, 8)),
                         np.ones((8, 8), dtype=np.int32), 0.95,
                         result, recommendation)
    assert expected in html
    assert recommendation.action in html
    assert "DeepLabV3 · ResNet-50" in html
    assert "LumenStone S2 v2 analogue · Bushveld validation pending" in html
    assert html.count('src="data:image/png;base64,') == 2
    # Check actual runtime asset references, including the Jinja/CSS layer.
    assert not re.search(r'(?:src|href)=[\"\'](?:https?:)?//', html)
    assert not re.search(r'url\([\"\']?(?:https?:)?//', html)
    assert "Full section, native resolution" in html  # the default mode_label
    if liberation is None:
        assert "MEASUREMENT DECLINED" in html


def test_live_field_mode_shows_its_measured_elapsed_time_not_a_fabricated_one():
    import numpy as np
    from PIL import Image
    from src.advisor import advise
    from src.modal import ModalResult

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 1, 64,
                         n_payload_particles=12)
    recommendation = advise(result, 0.95)

    with_timing = render.render(
        Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
        result, recommendation,
        mode_label="Live Field Mode, 512x512 field",
        elapsed_seconds=3.42,
    )
    assert "Live Field Mode, 512x512 field" in with_timing
    assert "3.4s from upload received to result" in with_timing

    without_timing = render.render(
        Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
        result, recommendation,
    )
    assert "from upload received" not in without_timing  # no fabricated number when unmeasured


def test_result_renders_opcua_publish_acknowledgement_and_refusal_states():
    import numpy as np
    from PIL import Image
    from src.advisor import advise
    from src.modal import ModalResult
    from dashboard.opcua import PublishStatus

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 1, 64,
                         n_payload_particles=12)
    recommendation = advise(result, 0.95)
    image = Image.new("RGB", (8, 8))
    labels = np.ones((8, 8), dtype=np.int32)
    applied = render.render(image, labels, 0.95, result, recommendation,
                            opcua_status=PublishStatus("applied", "consumer acknowledged and applied"))
    assert "OPC UA · PUBLISHED + ACKNOWLEDGED" in applied
    refused = render.render(image, labels, 0.95, result, recommendation,
                            opcua_status=PublishStatus("refused", "consumer refused stale record"))
    assert "OPC UA · CONSUMER REFUSED" in refused


def test_progress_render_marks_a_real_tile_and_reports_measured_state():
    import numpy as np
    from PIL import Image
    image = Image.new("RGB", (700, 600), "white")
    labels = np.full((600, 700), -1, dtype=np.int32)
    labels[:512, :512] = 1
    html = render.render_progress(image, labels, 1, 4, (0, 0, 512, 512), 0.82)
    assert "1 / 4 complete" in html
    assert "82.0%" in html
    assert "dark = not classified" in html
    assert "gold frame = tile just classified" in html


def test_evidence_render_labels_ground_truth_as_held_out_validation():
    import numpy as np
    from PIL import Image
    image = Image.new("RGB", (8, 8), "white")
    labels = np.zeros((8, 8), dtype=np.int32)
    html = render.render_evidence("test_01", image, labels, labels, 0.9, 12)
    assert "EVIDENCE VIEW · HELD-OUT VALIDATION" in html
    assert "Expert annotation · ground truth" in html
    assert "not a live or blind inference" in html
    assert "12 held-out sections" in html
    assert html.count('src="data:image/png;base64,') == 3


@pytest.mark.parametrize(
    "action, expected_count",
    [
        ("Marginal - verify before acting", 2),
        ("Continue at current setpoint", 0),
        ("Flag for manual review - no payload detected", 0),
    ],
)
def test_candidates_are_shown_only_for_marginal_verdicts(action, expected_count):
    recommendation = Recommendation(action=action, reason="test", confidence="high")
    candidates = render._candidates(None, recommendation)

    assert len(candidates) == expected_count
    if candidates:
        assert {candidate["action"] for candidate in candidates} == {
            "Continue at current setpoint",
            "Grind finer",
        }


def test_control_strip_shows_decision_evidence_and_plant_state():
    import numpy as np
    from PIL import Image

    from dashboard.control import CommandStatus
    from src.advisor import advise
    from src.modal import ModalResult

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 12, 64,
                         n_payload_particles=4)
    recommendation = advise(result, 0.95)
    lighting = {"stable": False, "abstained": False, "as_imaged": "Grind finer",
                "after_shift": "Marginal - verify before acting",
                "image": Image.new("RGB", (64, 64)), "shifted_image": Image.new("RGB", (64, 64))}
    plant = CommandStatus("held", 1.0, 1.0, "advisory is abstaining")
    html = render.render(Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
                         result, recommendation, plant=plant, lighting=lighting,
                         evidence_scope="six 512 px fields")
    assert "No recommendation — too few payload particles" in html
    assert "provisional floor 9" in html and "six 512 px fields" in html
    assert "need ≥" not in html
    assert "SIMULATED LIGHTING: UNSTABLE" in html
    assert "@media (max-width: 900px)" in html
    assert "PLANT · SIMULATED CIRCUIT" in html and ">HELD<" in html
    assert "no plant connected" in html


def test_strip_marks_the_unguarded_pipeline_and_a_no_change_continue():
    import numpy as np
    from PIL import Image

    from dashboard.control import CommandStatus
    from src.advisor import advise
    from src.modal import ModalResult

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 12, 64,
                         n_payload_particles=30)
    recommendation = advise(result, 0.95)
    assert recommendation.action == "Continue at current setpoint"
    lighting = {"stable": False, "abstained": False, "off": True,
                "as_imaged": recommendation.action, "after_shift": "check switched off",
                "image": Image.new("RGB", (64, 64)), "shifted_image": None}
    plant = CommandStatus("unchanged", 1.0, 1.0, "within specification: no command issued")
    html = render.render(Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
                         result, recommendation, plant=plant, lighting=lighting)
    assert "LIGHTING CHECK OFF · UNGUARDED" in html
    assert ">UNCHANGED<" in html and "1 → 1" in html


def test_evidence_scorecard_only_shows_for_the_checkpoint_that_produced_it():
    import json

    from src.segmentation import config

    reported = json.loads((config.REPORT_DIR / "s2_section_stats.json").read_text())["checkpoint_sha256"]
    scores = render.evidence_scores("test_01", reported)
    assert scores["mismatch"] is False and "section_iou" in scores
    other = render.evidence_scores("test_01", "0" * 64)
    assert other["mismatch"] is True and "section_iou" not in other


def test_evidence_view_names_mean_iou_and_hides_a_foreign_scorecard():
    import numpy as np
    from PIL import Image

    image = Image.new("RGB", (8, 8))
    mask = np.zeros((8, 8), dtype=np.int32)
    shown = render.render_evidence("test_01", image, mask, mask, 0.8, 12,
                                   scores={"mismatch": False, "section_iou": 0.41,
                                           "pooled_iou": 0.5725, "model_advice": "a",
                                           "expert_advice": "a", "agree": True})
    assert "Section mean IoU" in shown and "accuracy</div>" not in shown
    hidden = render.render_evidence("test_01", image, mask, mask, 0.8, 12,
                                    scores={"mismatch": True, "report_sha": "de7135a96541",
                                            "active_sha": "000000000000"})
    assert "Scorecard hidden" in hidden and "Section mean IoU" not in hidden


def test_full_section_is_advisory_only_and_says_so():
    import numpy as np
    from PIL import Image

    from dashboard.control import advisory_only_status
    from src.advisor import advise
    from src.modal import ModalResult

    status = advisory_only_status(1.0)
    assert (status.state, status.before, status.after) == ("held", 1.0, 1.0)
    assert "advisory only" in status.reason
    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.95, 0.05, 38, 64,
                         n_payload_particles=21)
    recommendation = advise(result, 0.95)
    assert recommendation.action == "Grind finer"
    html = render.render(Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
                         result, recommendation, plant=status, advisory_only=True,
                         evidence_scope="whole section, native resolution")
    assert "ADVISORY ONLY · NO LIGHTING CHECK" in html
    assert ">HELD<" in html and "1 → 1" in html
