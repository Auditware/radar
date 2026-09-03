"""Unit tests for the controller's reporting, gating, and baseline logic.

These cover the pure functions and the exit-code contract of print_write_outputs
(disk writes are stubbed) so the CI-gating behaviour can't silently regress.

Run from the controller directory: `python -m pytest tests/`
"""

import sys
import types
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers  # noqa: E402


# --- pure helpers ---------------------------------------------------------

@pytest.mark.parametrize(
    "severity,fail_on,expected",
    [
        ("Critical", "low", True),
        ("Low", "low", True),
        ("Low", "high", False),
        ("High", "high", True),
        ("Medium", "high", False),
        ("Critical", "none", False),
        ("High", "critical", False),
        ("Critical", "critical", True),
        ("bogus-severity", "low", True),
    ],
)
def test_meets_fail_threshold(severity, fail_on, expected):
    assert helpers.meets_fail_threshold(severity, fail_on) is expected


def test_location_sort_key_orders_by_file_then_numeric_line():
    locs = ["/a/z.rs:10:1-2", "/a/b.rs:2:5-9", "/a/b.rs:2:1-3", "/a/b.rs:10:1-2"]
    ordered = [l.split("/")[-1] for l in sorted(locs, key=helpers.location_sort_key)]
    assert ordered == ["b.rs:2:1-3", "b.rs:2:5-9", "b.rs:10:1-2", "z.rs:10:1-2"]


def test_baseline_fingerprint_and_apply():
    root = Path("/proj")
    findings = [
        {"name": "R1", "severity": "Low", "certainty": "Low", "description": "d",
         "locations": ["/proj/a.rs:10:3-9", "/proj/b.rs:5:1-2"]},
        {"name": "R2", "severity": "High", "certainty": "High", "description": "d",
         "locations": ["/proj/c.sol:20:1-5"]},
    ]
    fps = [fp for f in findings for fp in helpers.finding_fingerprints(f, root)]
    assert fps[0] == "R1::a.rs:10:3-9"
    remaining = helpers.apply_baseline(findings, set(fps[:2]), root)
    assert [f["name"] for f in remaining] == ["R2"]
    assert remaining[0]["locations"] == ["/proj/c.sol:20:1-5"]


def test_load_baseline_missing_file(tmp_path):
    assert helpers.load_baseline(tmp_path / "nope.json") == set()


# --- exit-code contract ---------------------------------------------------

def _run(results, fail_on="low", errors=None, baseline_path=None, write_baseline=False):
    with mock.patch.object(helpers, "save_json_output", lambda *a, **k: None), \
         mock.patch.object(helpers, "write_sarif_output", lambda *a, **k: None), \
         mock.patch.object(helpers, "save_markdown_output", lambda *a, **k: None), \
         mock.patch("pathlib.Path.mkdir", lambda *a, **k: None), \
         mock.patch("pathlib.Path.write_text", lambda *a, **k: None), \
         mock.patch("builtins.open", mock.mock_open()):
        try:
            helpers.print_write_outputs(
                results, {"sources": {"f": 1}}, False, None, "json", None,
                False, fail_on, errors or [], baseline_path, write_baseline,
            )
            return None
        except SystemExit as exc:
            return exc.code


def _finding(sev):
    return {"name": sev + "F", "severity": sev, "certainty": "Low",
            "description": "d", "locations": ["/a/b.rs:1:1-2"]}


def test_exit_clean_is_zero():
    assert _run([]) == 0


def test_exit_findings_default_low_is_one():
    assert _run([_finding("High")]) == 1


def test_exit_low_finding_with_fail_on_high_is_zero():
    assert _run([_finding("Low")], "high") == 0


def test_exit_fail_on_none_is_zero():
    assert _run([_finding("Critical")], "none") == 0


def test_exit_errors_take_precedence_two():
    assert _run([_finding("High")], "low", [{"name": "T", "error": "boom"}]) == 2
    assert _run([], "low", [{"name": "T", "error": "boom"}]) == 2


def test_write_baseline_exits_zero_without_gating():
    assert _run([_finding("Critical")], write_baseline=True) == 0


# --- scoped copies into the shared volume ---------------------------------

def test_copy_to_docker_mount_copies_a_scoped_file(tmp_path):
    """A --container-path pointing at one file used to be copied from /contract,
    the whole mount, which is a directory: shutil.copy2 raised 'Is a directory'."""
    src = tmp_path / "contract" / "src"
    src.mkdir(parents=True)
    (src / "lib.rs").write_text("fn main() {}")
    dst = tmp_path / "radar_data" / "contract" / "src" / "lib.rs"

    helpers.copy_to_docker_mount(src / "lib.rs", dst, "file")

    assert dst.read_text() == "fn main() {}"


def test_copy_to_docker_mount_copies_a_scoped_folder(tmp_path):
    src = tmp_path / "contract" / "programs" / "one"
    src.mkdir(parents=True)
    (src / "lib.rs").write_text("fn one() {}")
    sibling = tmp_path / "contract" / "programs" / "two"
    sibling.mkdir(parents=True)
    (sibling / "lib.rs").write_text("fn two() {}")
    dst = tmp_path / "radar_data" / "contract" / "programs" / "one"

    helpers.copy_to_docker_mount(src, dst, "folder")

    # Only the scoped program, not its sibling.
    assert (dst / "lib.rs").read_text() == "fn one() {}"
    assert not (dst.parent / "two").exists()


def test_main_copies_the_scoped_path_not_the_whole_mount(monkeypatch):
    """main() derives path_type from --container-path, so it must copy that path.
    Sourcing from /contract failed outright for a file and copied the wrong tree
    for a subdirectory.

    `main` imports controller.api, which pulls in requests and reads env at import
    time. Neither belongs in this suite - it is meant to run on a bare pytest with
    no runtime dependencies - so the module is stubbed at the import boundary."""
    fake_api = types.ModuleType("api")
    fake_api.generate_ast_for_file_or_folder = lambda *a: {"ast": {}}
    fake_api.run_scan = lambda *a: None
    fake_api.poll_results = lambda *a: ([], [])
    monkeypatch.setitem(sys.modules, "api", fake_api)
    monkeypatch.delitem(sys.modules, "main", raising=False)
    import main  # noqa: PLC0415

    scoped = Path("/contract/src/lib.rs")
    copied = []
    monkeypatch.setattr(main, "check_path", lambda path: "file")
    monkeypatch.setattr(
        main, "copy_to_docker_mount", lambda src, dst, kind: copied.append((src, dst))
    )
    monkeypatch.setattr(main, "print_write_outputs", lambda *a, **k: None)
    monkeypatch.setattr(
        main, "parse_arguments", lambda: mock.Mock(
            container_path=str(scoped), output=None, templates=None, path=None,
            ast=False, ignore=None, debug=False, fail_on="low",
            baseline=None, write_baseline=False,
        )
    )

    main.main()

    assert copied == [(scoped, Path("/radar_data/contract/src/lib.rs"))]


# --- a clean scan still writes the promised artefact -----------------------

@pytest.mark.parametrize(
    "output_type,expected",
    [("json", "[]"), ("md", "No results found."), ("sarif", '"version"')],
)
def test_clean_scan_writes_an_empty_output_file(output_type, expected, tmp_path, monkeypatch):
    """radar used to write nothing for json/md when there were no findings, while
    the CLI copied the path out and reported 'Results written to ...' regardless,
    leaving the caller a success message and no file."""
    written = tmp_path / f"output.{output_type}"
    monkeypatch.setattr(
        helpers, "Path", lambda *a: written if str(a[0]).startswith("/radar_data/output") else Path(*a)
    )

    with mock.patch.object(helpers, "container_output_file_path", written, create=True):
        try:
            helpers.print_write_outputs(
                [], {"sources": {"f": 1}}, False, None, output_type, None,
                False, "low", [], None, False,
            )
        except SystemExit as exc:
            assert exc.code == 0

    assert written.exists(), f"no {output_type} file written for a clean scan"
    assert expected in written.read_text()
