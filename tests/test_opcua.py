from dashboard.opcua import record_parameters


def test_stale_record_contract_is_explicit_and_short_lived():
    fresh = record_parameters({"association_index": 72.0}, stale=False, now=100.0)
    stale = record_parameters({"association_index": 72.0}, stale=True, now=100.0)
    assert fresh["emitted_at"] == 100.0
    assert fresh["valid_for_seconds"] == 30.0
    assert stale["emitted_at"] == 98.0
    assert stale["valid_for_seconds"] == 0.5
    assert stale["source"] == "KHANYA dashboard result"
    assert stale["advisory_influenced"] is False
