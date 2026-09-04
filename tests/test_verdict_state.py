"""Amber is reserved for the two states where the advisor declines to decide.
A confident continue is green, a confident grind is red - neither may borrow
the colour that means "do not act on this yet".
"""
import pytest

from src.advisor import verdict_state


@pytest.mark.parametrize("action,expected_class", [
    ("Continue at current setpoint", ""),
    ("Grind finer", "grind"),
    ("Marginal - verify before acting", "hold"),
    ("Flag for manual review - no payload detected", "hold"),
    ("Flag for manual review - liberation not measurable", "hold"),
    ("No recommendation - insufficient ore in field", "hold"),
])
def test_only_abstaining_states_render_amber(action, expected_class):
    css_class, _label = verdict_state(action)
    assert css_class == expected_class
