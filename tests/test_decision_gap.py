from src import advisor
from src.decision_gap import classify


def test_every_advisor_abstention_counts_as_a_hedge_not_an_error():
    for prefix in advisor.ABSTAINING_PREFIXES:
        assert classify("Grind finer", f"{prefix} - anything") == "flagged"


def test_confident_continue_against_a_grind_reference_is_unsafe():
    assert classify("Grind finer", "Continue at current setpoint") == "unsafe"
