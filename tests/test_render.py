"""Contracts for the offline Stitch renderer.

These test the two failure modes a visual inspection could easily miss: a
missing vendored asset must say how to repair the build, and only a genuinely
marginal verdict may offer the two equally weighted candidate actions.
"""
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
    assert "st.components.v1.html(" in app_source
    assert "KHANYA_CSS" not in app_source


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
