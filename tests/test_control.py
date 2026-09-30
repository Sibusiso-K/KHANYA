import pytest

from dashboard.control import REGRIND_HEAD, command_for, command_parameters, send_command


def test_only_grind_finer_commands_the_regrind_tag():
    assert command_for("Grind finer")[0] == 1.0
    for abstaining in (
                       "Continue at current setpoint","Marginal - verify before acting",
                       "Flag for manual review - low payload signal",
                       "No recommendation - insufficient ore in field",
                       "Adjust reagent dosage - raise depressant",
                       "an action advise() cannot produce today"):
        value, reason = command_for(abstaining)
        assert value is None and reason


def test_command_record_carries_the_freshness_contract():
    fresh = command_parameters(1.0, "Grind finer", stale=False, now=100.0)
    stale = command_parameters(1.0, "Grind finer", stale=True, now=100.0)
    assert fresh["values"] == {REGRIND_HEAD: 1.0}
    assert (fresh["emitted_at"], fresh["valid_for_seconds"]) == (100.0, 30.0)
    assert (stale["emitted_at"], stale["valid_for_seconds"]) == (98.0, 0.5)
    assert fresh["advisory_influenced"] is False


def test_abstaining_advisory_holds_without_opening_a_connection():
    status = send_command("Marginal - verify before acting", before=1.0)
    assert (status.state, status.before, status.after, status.endpoint) == ("held", 1.0, 1.0, None)


def _wire_or_skip(status):
    if status.state == "unavailable":
        pytest.skip(status.reason)
    return status


def test_fresh_command_moves_the_setting_over_real_opc_ua():
    pytest.importorskip("asyncua")
    status = _wire_or_skip(send_command("Grind finer", before=0.0))
    assert (status.state, status.before, status.after) == ("applied", 0.0, 1.0)
    assert status.endpoint


def test_continue_means_no_change_whatever_the_current_setting():
    for before in (0.0, 1.0):
        status = send_command("Continue at current setpoint", before=before)
        assert (status.state, status.before, status.after, status.endpoint) == (
            "unchanged", before, before, None)


def test_consumer_starts_from_the_plants_current_value():
    pytest.importorskip("asyncua")
    # A refused command leaves the consumer's parameter untouched, so it must
    # still read the seeded 1.0, not the client's default 0.0.
    status = _wire_or_skip(send_command("Grind finer", before=1.0, stale=True))
    assert (status.state, status.before, status.after) == ("refused", 1.0, 1.0)


def test_stale_command_is_refused_and_the_setting_does_not_move():
    pytest.importorskip("asyncua")
    status = _wire_or_skip(send_command("Grind finer", before=0.0, stale=True))
    assert (status.state, status.before, status.after) == ("refused", 0.0, 0.0)
