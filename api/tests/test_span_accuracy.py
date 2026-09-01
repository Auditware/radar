"""Source-span accuracy for the Rust AST enrichment.

Findings are only actionable if their reported line points at the code that
caused them. Spans are not taken from the parser: the enrichment scans the
source for each identifier and hands successive occurrences to successive AST
nodes, which is only correct while the walk follows source order.

Two invariants are pinned here:

* a struct field's span lands on the line where that field is declared - the
  case the original span bug got wrong (repeated field types all collapsing
  onto the first occurrence); and
* a `where` clause is attributed to the line it is written on. The parser nests
  the where-clause under `generics`, which is emitted before the parameter list
  and return type, so a declaration-order walk gives the where-clause and the
  return type each other's positions.

Both parse Rust for real, so this is marked `active_runtime`.
"""

import re

import pytest
import yaml

from tests.check_scoping import MOCKS, TEMPLATES
from utils.ast import generate_ast_for_rust_file


def _anchor_mock_sources():
    anchor = {
        p.stem
        for p in TEMPLATES.glob("*.yaml")
        if (yaml.safe_load(p.read_text()) or {}).get("accent") == "anchor"
    }
    return [
        f
        for f in sorted(MOCKS.glob("*/*/src/lib.rs"))
        if f.parent.parent.parent.name in anchor
    ]


def _collect(node, out, path="", want=None):
    """Collect (ident, line, access_path) for ident nodes matching `want`."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if (
                key == "ident"
                and isinstance(value, str)
                and isinstance(node.get("src"), dict)
                and (want is None or want(path, value))
            ):
                out.append((value, node["src"]["line"], path))
            if isinstance(value, (dict, list)):
                _collect(value, out, child, want)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _collect(item, out, f"{path}[{index}]", want)


FIELD_PATH = re.compile(r"\.struct\.fields\.named\[\d+\]$")


@pytest.mark.active_runtime
@pytest.mark.parametrize(
    "source", _anchor_mock_sources(), ids=lambda p: p.parent.parent.parent.name
)
def test_struct_field_spans_land_on_their_declaration(source):
    ast = generate_ast_for_rust_file(source)["ast"]
    lines = source.read_text().splitlines()

    fields = []
    _collect(ast, fields, want=lambda path, _v: bool(FIELD_PATH.search(path)))

    for name, line, _path in fields:
        assert 1 <= line <= len(lines), f"{name}: span line {line} out of range"
        assert re.search(rf"\b{re.escape(name)}\s*:", lines[line - 1]), (
            f"field '{name}' span points at line {line} "
            f"({lines[line - 1].strip()!r}), which is not its declaration"
        )


@pytest.mark.active_runtime
def test_where_clause_is_not_given_the_return_types_position(tmp_path):
    source = tmp_path / "lib.rs"
    source.write_text(
        "pub trait Marker {}\n"          # 1
        "\n"                             # 2
        "pub fn helper<T>(input: T) -> T\n"  # 3
        "where\n"                        # 4
        "    T: Marker,\n"               # 5
        "{\n"                            # 6
        "    input\n"                    # 7
        "}\n"                            # 8
    )
    ast = generate_ast_for_rust_file(source)["ast"]

    found = []
    _collect(ast, found, want=lambda _p, v: v == "T")
    by_path = {path: line for _v, line, path in found}

    where = next((l for p, l in by_path.items() if "where_clause" in p), None)
    output = next((l for p, l in by_path.items() if ".output" in p), None)

    assert where == 5, f"where-clause T should be line 5, got {where}"
    assert output == 3, f"return-type T should be line 3, got {output}"
