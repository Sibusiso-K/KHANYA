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
    assert "render.render_landing()" in app_source
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

    assert "Awaiting a reflected-light micrograph" in html
    assert "REEFPRINT :: KHANYA" in html
    assert "No network required" in html
    assert "Dr. K. Vance" not in html
    assert "ISO/IEC 17025" not in html
    assert "DISPATCH" not in html


def test_missing_static_asset_names_the_repair_step():
    with pytest.raises(FileNotFoundError, match="compile step"):
        render._read_text("not-a-real-static-asset.css")


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
