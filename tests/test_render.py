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
    assert "RUN HELD-OUT EXAMPLE" in app_source
    assert "benchmark:test_01" in app_source
    assert "Developer and simulator controls" in app_source
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

    assert "From polished section to process insight" in html
    # The app shell owns branding; the embedded analysis fragment must not
    # render a second header when Streamlit places it below the controls.
    assert '<header class="top">' not in html
    app_source = (Path(__file__).resolve().parents[1] / "dashboard" / "app.py").read_text(encoding="utf-8")
    assert "reefprint-masthead" in app_source
    assert app_source.index("uploaded = st.file_uploader") < app_source.index(
        "# Place result/progress slots after the input card"
    )
    assert "Sample &amp; interval" in html
    assert "Geology &amp; spatial context" in html
    assert "AI phase analysis" in html
    assert "0.4543" in html and "0.7716" in html
    assert "Magnetite" in html and "IoU = 0.000" in html
    assert "SCHEMATIC" in html and "NO LIVE PLANT" in html
    assert "@media(max-width:620px)" in html
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
                         0.8, liberation, 1, 64)
    recommendation = advise(result, 0.95)
    html = render.render(Image.new("RGB", (8, 8)),
                         np.ones((8, 8), dtype=np.int32), 0.95,
                         result, recommendation)
    assert expected in html
    assert recommendation.action in html
    assert "DeepLabV3 · ResNet-50" in html
    assert "No simulator command recorded for this run." in html
    assert "LumenStone S2 v2 analogue · Bushveld validation pending" in html
    assert html.count('src="data:image/png;base64,') == 2
    # Check actual runtime asset references, including the Jinja/CSS layer.
    assert not re.search(r'(?:src|href)=[\"\'](?:https?:)?//', html)
    assert not re.search(r'url\([\"\']?(?:https?:)?//', html)
    assert "Full section, native resolution" in html  # the default mode_label
    assert "GEOLOGY / 3D CONTEXT" in html
    assert ".result-grid > .spatial-context { grid-column:2; grid-row:1; }" in html
    assert "SCHEMATIC ONLY" in html
    assert "FIELD XRF" in html and "NO READINGS" in html
    assert "VALIDATION · HELD-OUT S2" in html
    assert "MODEL OUTPUT → PROCESS SCENARIO" in html
    assert "SIMULATION ONLY · NO LIVE CONTROL" in html
    assert "@media(max-width:680px)" in html
    if liberation is None:
        assert "MEASUREMENT DECLINED" in html


def test_live_field_mode_shows_its_measured_elapsed_time_not_a_fabricated_one():
    import numpy as np
    from PIL import Image
    from src.advisor import advise
    from src.modal import ModalResult

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 1, 64)
    recommendation = advise(result, 0.95)

    with_timing = render.render(
        Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
        result, recommendation,
        mode_label="Live Field Mode, 512x512 field",
        elapsed_seconds=3.42,
    )
    assert "Live Field Mode, 512x512 field" in with_timing
    assert "3.4s end to end" in with_timing

    without_timing = render.render(
        Image.new("RGB", (8, 8)), np.ones((8, 8), dtype=np.int32), 0.95,
        result, recommendation,
    )
    assert "end to end" not in without_timing  # no fabricated number when unmeasured


def test_result_renders_opcua_publish_acknowledgement_and_refusal_states():
    import numpy as np
    from PIL import Image
    from src.advisor import advise
    from src.modal import ModalResult
    from dashboard.opcua import PublishStatus

    result = ModalResult({"chalcopyrite": 1.0}, {"payload": 1.0}, 0.8, 0.95, 1, 64)
    recommendation = advise(result, 0.95)
    image = Image.new("RGB", (8, 8))
    labels = np.ones((8, 8), dtype=np.int32)
    applied = render.render(
        image, labels, 0.95, result, recommendation,
        opcua_status=PublishStatus("applied", "consumer acknowledged and applied"),
        sample_title="LumenStone S2 held-out test_01",
        sample_caption="Not South African ore.",
        simulation_preview={"parameter": "regrind_enabled", "before": "0", "after": "1", "state": "applied"},
    )
    assert "OPC UA · PUBLISHED + ACKNOWLEDGED" in applied
    assert "regrind_enabled: 0 → 1 · APPLIED" in applied
    assert "LumenStone S2 held-out test_01" in applied
    assert "Not South African ore." in applied
    assert "SIMULATION ONLY · NO LIVE CONTROL" in applied
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
