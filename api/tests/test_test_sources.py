"""Telling test code from shipped code.

Pure-Python, no parser and no Django, so it runs in the fast suite.
"""

import pytest

from utils.test_sources import (
    is_test_attribute,
    is_test_item,
    is_test_path,
    strip_test_items,
)


def attr(**meta):
    return {"style": "outer", "meta": meta}


def path_attr(*segments):
    return attr(path={"segments": [{"ident": s} for s in segments]})


def cfg_attr(tokens):
    return attr(list={"path": {"segments": [{"ident": "cfg"}]}, "tokens": tokens})


@pytest.mark.parametrize(
    "path",
    [
        "programs/foo/tests/integration.rs",
        "tests/common/mod.rs",
        "rust/tests/slyvault/src/lib.rs",  # a whole test crate
        "src/test/helpers.rs",
        "src/tests.rs",
        "src/test_utils.rs",
        "src/vault_test.rs",
        "src/vault_tests.rs",
        "src/vault.test.rs",
    ],
)
def test_paths_recognised_as_tests(path):
    assert is_test_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "programs/foo/src/lib.rs",
        "src/instructions/attest.rs",
        # `contest` and `latest` end in "test" but are not tests; matching on
        # whole path segments and known suffixes rather than substrings is what
        # keeps them out.
        "src/contest.rs",
        "src/latest/state.rs",
        "benches/throughput.rs",   # a benchmark is not asserting correctness
        "examples/transfer.rs",    # examples are code users are told to copy
    ],
)
def test_paths_not_recognised_as_tests(path):
    assert not is_test_path(path)


@pytest.mark.parametrize(
    "attribute",
    [
        path_attr("test"),
        path_attr("bench"),
        path_attr("tokio", "test"),
        path_attr("actix_rt", "test"),
        cfg_attr([{"ident": "test"}]),
        # `#[cfg(any(test, feature = "x"))]` nests it
        cfg_attr([{"ident": "any"}, {"group": {"tokens": [{"ident": "test"}]}}]),
    ],
)
def test_attributes_recognised_as_tests(attribute):
    assert is_test_attribute(attribute)


@pytest.mark.parametrize(
    "attribute",
    [
        path_attr("account"),
        path_attr("derive"),
        cfg_attr([{"ident": "feature"}]),
        cfg_attr([{"ident": "target_os"}]),
    ],
)
def test_attributes_not_recognised_as_tests(attribute):
    assert not is_test_attribute(attribute)


def test_is_test_item_reads_the_items_own_attributes():
    assert is_test_item({"mod": {"ident": "tests", "attrs": [cfg_attr([{"ident": "test"}])]}})
    assert not is_test_item({"fn": {"ident": "transfer", "attrs": []}})
    assert not is_test_item({"fn": {"ident": "transfer"}})


def test_strip_removes_test_items_and_keeps_the_rest():
    items = [
        {"fn": {"ident": "transfer"}},
        {"mod": {"ident": "tests", "attrs": [cfg_attr([{"ident": "test"}])]}},
        {"fn": {"ident": "helper", "attrs": [path_attr("test")]}},
    ]
    kept = strip_test_items(items)
    assert [list(i.values())[0]["ident"] for i in kept] == ["transfer"]


def test_strip_recurses_into_nested_modules():
    """`#[cfg(test)] mod tests` normally sits inside the module it tests."""
    items = [
        {
            "mod": {
                "ident": "instructions",
                "items": [
                    {"fn": {"ident": "transfer"}},
                    {"mod": {"ident": "tests", "attrs": [cfg_attr([{"ident": "test"}])]}},
                ],
            }
        }
    ]
    kept = strip_test_items(items)
    inner = kept[0]["mod"]["items"]
    assert [list(i.values())[0]["ident"] for i in inner] == ["transfer"]


def test_strip_does_not_mutate_its_input():
    items = [{"mod": {"ident": "tests", "attrs": [cfg_attr([{"ident": "test"}])]}}]
    strip_test_items(items)
    assert len(items) == 1


def test_directories_are_judged_relative_to_the_scan_root():
    """A checkout that happens to live under a `tests/` directory still scans.

    Judged absolutely, every file below `~/work/tests/my-program` reads as test
    code and the scan comes back empty with nothing to explain it.
    """
    root = "/home/dev/work/tests/my-program"
    assert not is_test_path(f"{root}/src/lib.rs", relative_to=root)
    # ...while a `tests/` directory *inside* that project is still excluded.
    assert is_test_path(f"{root}/tests/integration.rs", relative_to=root)


def test_path_outside_the_root_falls_back_to_the_whole_path():
    assert is_test_path("/elsewhere/tests/x.rs", relative_to="/project")
