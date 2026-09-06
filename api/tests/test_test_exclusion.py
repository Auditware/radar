"""End-to-end gate: excluding test code must not move the findings that remain.

`strip_test_items` runs after span enrichment, because enrichment hands each
node the nth textual occurrence of its identifier. Pruning first would renumber
every occurrence below the removed block, so a `#[cfg(test)] mod tests` written
above the production code would shift the findings under it - silently, since
the finding still fires, just on the wrong line.

The fixture puts the test module above the production code precisely so this
gate fails if that ordering is ever reversed.
"""

from pathlib import Path

import pytest

from utils.ast import generate_ast_for_rust_file

FIXTURE = Path(__file__).resolve().parent / "test_exclusion" / "cfg_test_above_production.rs"


def _idents(items):
    """Every (ident, line) the enriched AST carries, flattened."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            src = node.get("src")
            if node.get("ident") and isinstance(src, dict):
                found.append((node["ident"], src["line"]))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(items)
    return found


@pytest.mark.active_runtime
def test_pruning_does_not_shift_the_spans_of_production_code():
    with_tests = generate_ast_for_rust_file(FIXTURE, include_tests=True)["ast"]
    without = generate_ast_for_rust_file(FIXTURE, include_tests=False)["ast"]

    kept = dict(_idents(without))
    full = dict(_idents(with_tests))

    assert kept, "pruning removed everything"
    for ident, line in kept.items():
        assert full[ident] == line, (
            f"{ident!r} moved from line {full[ident]} to {line} when test code "
            f"was excluded - items are being pruned before span enrichment"
        )


@pytest.mark.active_runtime
def test_pruning_removes_the_test_module_and_keeps_production():
    without = generate_ast_for_rust_file(FIXTURE, include_tests=False)["ast"]
    idents = {ident for ident, _ in _idents(without)}

    assert "withdraw" in idents, "production handler was removed"
    assert "Withdraw" in idents, "production accounts struct was removed"
    assert "tests" not in idents, "#[cfg(test)] module survived"
    assert "reuses_a_pda_and_skips_the_owner_check" not in idents, "test fn survived"


@pytest.mark.active_runtime
def test_including_tests_keeps_the_test_module():
    with_tests = generate_ast_for_rust_file(FIXTURE, include_tests=True)["ast"]
    idents = {ident for ident, _ in _idents(with_tests)}
    assert "tests" in idents and "reuses_a_pda_and_skips_the_owner_check" in idents
