"""Placeholder — reefprint.trust. What is left of it.

Rule 2 is built: ``test_trust_split.py``. Rule 3: ``test_trust_baseline.py``.
Rule 5: ``test_trust_abstain.py``. Rules 4 (honest n) and the week-3 and week-4
gates are still prose, and still fail here on purpose.
"""

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


def test_no_silent_failure_under_degraded_input():
    """**Week-4 gate.** Defocus, glare, poor polish, wrong exposure, empty field.

    Every degraded input produces either a result or a stated refusal. Never a confident number.
    """
    pytest.fail("NOT BUILT — trust: degraded-input behaviour, week-4 gate")
