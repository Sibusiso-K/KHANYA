"""The preflight's REEFPRINT pin: by content, independent of line endings."""
from src.preflight import check_offline_config, reefprint_integrate_sha256


def _tree(root, body):
    folder = root / "reefprint" / "integrate"
    folder.mkdir(parents=True)
    (folder / "opcua_server.py").write_bytes(body)
    (folder / "advisory.py").write_bytes(b"A = 1\n")
    return root


def test_windows_and_unix_checkouts_of_the_same_code_match(tmp_path):
    unix = _tree(tmp_path / "unix", b"x = 1\ny = 2\n")
    windows = _tree(tmp_path / "windows", b"x = 1\r\ny = 2\r\n")
    assert reefprint_integrate_sha256(unix) == reefprint_integrate_sha256(windows)


def test_any_code_change_breaks_the_pin(tmp_path):
    before = _tree(tmp_path / "before", b"x = 1\n")
    after = _tree(tmp_path / "after", b"x = 2\n")
    assert reefprint_integrate_sha256(before) != reefprint_integrate_sha256(after)


def test_committed_streamlit_config_keeps_telemetry_off():
    ok, detail = check_offline_config()
    assert ok, detail
