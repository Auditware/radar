"""Tests for inline finding suppression markers."""

from utils.suppression import filter_suppressed_locations, is_suppressed


def _write(tmp_path, lines):
    f = tmp_path / "lib.rs"
    f.write_text("\n".join(lines))
    return str(f)


def test_bare_next_line_suppresses_any_rule(tmp_path):
    f = _write(tmp_path, ["// radar-disable-next-line", "flagged"])
    assert is_suppressed(f, 2, "Missing Signer Check")


def test_next_line_with_rule_only_suppresses_that_rule(tmp_path):
    f = _write(tmp_path, ["// radar-disable-next-line Missing_Signer_Check", "flagged"])
    assert is_suppressed(f, 2, "Missing Signer Check")
    assert not is_suppressed(f, 2, "Missing Owner Check")


def test_disable_line_on_same_line(tmp_path):
    f = _write(tmp_path, ["code // radar-disable-line missing-signer-check"])
    assert is_suppressed(f, 1, "Missing Signer Check")


def test_no_marker_is_not_suppressed(tmp_path):
    f = _write(tmp_path, ["just code", "more code"])
    assert not is_suppressed(f, 2, "Missing Signer Check")


def test_missing_file_does_not_suppress():
    assert not is_suppressed("/no/such/file.rs", 1, "Anything")


def test_filter_keeps_unsuppressed(tmp_path):
    f = _write(
        tmp_path,
        ["// radar-disable-next-line", "flagged_a", "flagged_b"],
    )
    locs = [f + ":2:1-2", f + ":3:1-2"]
    kept = filter_suppressed_locations(locs, "Some Rule")
    assert kept == [f + ":3:1-2"]


def test_filter_passes_through_unparseable_locations():
    locs = ["not-a-location"]
    assert filter_suppressed_locations(locs, "R") == locs
