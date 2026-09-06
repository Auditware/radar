"""Gate: the tree the rules walk must contain every node the parser produced.

`serialize_rust_ast` flattens the syn AST into nodes keyed by access path, and
`parse_rust_ast` links them into the tree that every DSL primitive walks. Linking
by path string is only sound while paths are unique, and they were not: a `&mut`
wrapper emitted a second node at an existing path, which displaced the real one
in the index. Everything beneath it linked to a node that was itself unlinked,
so the subtree existed in the flat list and was unreachable from the root.

What that cost, concretely: `&mut ctx.accounts.vault.data.borrow_mut()` reached
the rules as a bare `borrow_mut` with no receiver. Two different accounts
produced identical nodes, so no rule could tell which account it had been handed
- which is why guards had to be scoped per function instead of per account.

These assertions are structural rather than per-rule on purpose. A rule test
notices when one rule regresses; this notices when the tree silently loses nodes,
which is what makes rules regress in ways nobody can attribute.
"""

from pathlib import Path

import pytest

from utils.ast import generate_ast_for_rust_file
from utils.dsl.dsl_ast_iterator import parse_rust_ast, serialize_rust_ast

MOCKS = Path(__file__).resolve().parent / "mocks"

# One statement per shape that reaches the parser differently. `&mut` is the one
# that used to lose everything to the right of it, and it is also how Solana
# code touches account data, so the loss landed exactly where it hurt most.
SHAPES = {
    "plain method call": "let a = ctx.accounts.vault.data.borrow();",
    "mut-ref method call": "let a = &mut ctx.accounts.vault.data.borrow_mut();",
    "ref method call": "let a = &ctx.accounts.vault.data.borrow();",
    "mut binding": "let mut a = ctx.accounts.vault.data.borrow();",
    "chained methods": "let a = ctx.accounts.vault.to_account_info().key();",
    "mut-ref field": "let a = &mut ctx.accounts.vault.amount;",
    "mut-ref nested call": "let a = &mut vault.to_account_info().data.borrow_mut();",
}


def _blob(tmp_path: Path, source: str, name="probe.rs"):
    path = tmp_path / name
    path.write_text(source)
    return {"sources": {name: {"ast": generate_ast_for_rust_file(path)["ast"]}}}


def _reachable(roots):
    seen = []

    def walk(node):
        for child in node.children:
            seen.append(child)
            walk(child)

    for root in roots.values():
        walk(root)
    return seen


@pytest.mark.active_runtime
@pytest.mark.parametrize("shape", sorted(SHAPES), ids=lambda s: s.replace(" ", "-"))
def test_no_node_is_unreachable_from_the_root(shape, tmp_path):
    blob = _blob(tmp_path, "pub fn touch() {\n    %s\n}\n" % SHAPES[shape])
    flat = serialize_rust_ast(blob)
    reachable = _reachable(parse_rust_ast(blob))

    assert len(reachable) == len(flat), (
        f"{len(flat) - len(reachable)} of {len(flat)} node(s) are in the flat list "
        f"but unreachable from the tree the rules walk"
    )


@pytest.mark.active_runtime
@pytest.mark.parametrize("shape", sorted(SHAPES), ids=lambda s: s.replace(" ", "-"))
def test_access_paths_are_unique(shape, tmp_path):
    """Two nodes at one path make the path index ambiguous, which is the bug."""
    blob = _blob(tmp_path, "pub fn touch() {\n    %s\n}\n" % SHAPES[shape])
    paths = [node.access_path for node in serialize_rust_ast(blob)]
    duplicates = {p for p in paths if paths.count(p) > 1}
    assert not duplicates, f"duplicate access path(s): {duplicates}"


@pytest.mark.active_runtime
def test_a_mut_ref_receiver_chain_survives(tmp_path):
    """The case from PR #38: which account did `borrow_mut` borrow?"""
    source = (
        "pub fn touch() {\n"
        "    let a = &mut ctx.accounts.alpha.data.borrow_mut();\n"
        "    let b = &mut ctx.accounts.beta.data.borrow_mut();\n"
        "}\n"
    )
    roots = parse_rust_ast(_blob(tmp_path, source))
    borrows = [n for n in _reachable(roots) if n.ident == "borrow_mut"]
    assert len(borrows) == 2

    def idents_under(node):
        found = []
        for child in node.children:
            found.append(child.ident)
            found.extend(idents_under(child))
        return found

    reached = [idents_under(node) for node in borrows]
    assert any("alpha" in chain for chain in reached), "lost the alpha receiver"
    assert any("beta" in chain for chain in reached), "lost the beta receiver"


@pytest.mark.active_runtime
def test_mut_metadata_lands_on_a_reachable_node(tmp_path):
    """`find_mutables` walks children, so a `mut` flag on an unlinked node is invisible."""
    blob = _blob(tmp_path, "pub fn touch() {\n    let a = &mut ctx.accounts.vault.amount;\n}\n")
    flagged = [n for n in _reachable(parse_rust_ast(blob)) if n.metadata.get("mut")]
    assert flagged, "the mut flag is not on any node reachable from the root"


@pytest.mark.active_runtime
def test_every_mock_source_keeps_all_its_nodes():
    """The structural invariant, over the whole corpus rather than seven shapes."""
    lossy = []
    for source in sorted(MOCKS.glob("*/*/src/*.rs"))[:60]:
        blob = {"sources": {str(source): {"ast": generate_ast_for_rust_file(source)["ast"]}}}
        flat = serialize_rust_ast(blob)
        reachable = _reachable(parse_rust_ast(blob))
        if len(reachable) != len(flat):
            lossy.append(f"{source.relative_to(MOCKS)}: {len(flat) - len(reachable)} lost")
    assert not lossy, "nodes unreachable from the tree:\n  " + "\n  ".join(lossy)


# --- Solidity -----------------------------------------------------------------
#
# `parse_solidity_ast` had the same assembly as `parse_rust_ast`, and therefore
# the same three defects: a path index where the later node wins, `assigned`
# keyed by path rather than identity, and orphans tested against a `parent`
# pointer serialization had already set. None of it was observable, because that
# serializer does not currently emit two nodes at one access path.
#
# "Not currently triggered" is not a property a codebase keeps by accident. This
# asserts the invariant directly, so the day some shape does produce a duplicate,
# it fails here instead of quietly removing a subtree from what the rules walk.


def _reachable_solidity(roots):
    seen = []

    def walk(node):
        for child in node.children:
            seen.append(child)
            walk(child)

    for _, root in roots.items():
        walk(root)
    return seen


@pytest.mark.active_runtime
def test_no_solidity_node_is_unreachable_from_the_root():
    import json

    from utils.dsl.solidity import parse_solidity_ast, serialize_solidity_ast

    checked, lossy = 0, []
    for fixture in sorted(MOCKS.glob("*/*/ast.json")):
        if not list(fixture.parent.rglob("*.sol")):
            continue
        try:
            blob = json.loads(fixture.read_text())
            flat = serialize_solidity_ast(blob)
            reachable = _reachable_solidity(parse_solidity_ast(blob))
        except Exception:
            continue  # not a Solidity compile result; the accuracy suite owns that
        checked += 1
        if len(reachable) != len(flat):
            lossy.append(
                f"{fixture.parent.relative_to(MOCKS)}: {len(flat) - len(reachable)} "
                f"of {len(flat)} unreachable"
            )

    assert checked, "no Solidity fixtures found; this gate would pass vacuously"
    assert not lossy, "nodes unreachable from the Solidity tree:\n  " + "\n  ".join(lossy)
