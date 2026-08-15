"""Placeholder — reefprint.trust."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_conformal_coverage_holds_per_held_out_locality():
    """**Week-3 gate.** Not pooled — per locality. Rule 2."""
    pytest.fail("NOT BUILT — trust: conformal coverage per locality, week-3 gate")


def test_reported_coverage_interval_matches_honest_n():
    """Rule 4. Coverage SD is sqrt(0.9 * 0.1 / n_cal): ~3.0 pp at n_cal = 100, ~6.7 pp at 20.

    A claimed band tighter than the arithmetic allows is a claim the arithmetic will refute in
    front of a judge.
    """
    pytest.fail("NOT BUILT — trust: coverage interval sizing")


def test_abstention_emits_a_conservative_default_with_a_reason():
    """Rule 5. Never "unknown".

    Blind spot 1: abstention fires exactly when it is least safe, because novel texture triggers
    the OOD gate and novel texture *is* an ore transition — the moment when holding the last
    setpoint is the worst available action.
    """
    pytest.fail("NOT BUILT — trust: conservative-default abstention")


def test_abstention_rate_is_reported_conditioned_on_ore_change_events():
    """An aggregate abstention rate hides the only conditional that matters."""
    pytest.fail("NOT BUILT — trust: conditional abstention reporting")


def test_no_silent_failure_under_degraded_input():
    """**Week-4 gate.** Defocus, glare, poor polish, wrong exposure, empty field.

    Every degraded input produces either a result or a stated refusal. Never a confident number.
    """
    pytest.fail("NOT BUILT — trust: degraded-input behaviour, week-4 gate")
