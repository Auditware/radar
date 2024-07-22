from pathlib import Path
from utils.ast import (
    generate_aggregate_program_ast,
    generate_anchor_project_ast,
    generate_anchor_project_derived_program_ast,
)

mock_rust_syn_ast = {
    "ast": {"items": [{"type": "function", "name": "main", "src": "fn main() {}"}]},
    "metadata": {"program_info": {"name": "test_program", "version": "0.1.0"}},
}


def test_generate_anchor_project_ast(monkeypatch):
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_anchor_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    source_path = Path("tests/mocks/anchor-test")
    result = generate_anchor_project_ast(source_path)

    assert isinstance(result, dict)
    assert "sources" in result
    assert (
        result["metadata"]["anchor_toml_path"] == "tests/mocks/anchor-test/Anchor.toml"
    )


def test_generate_anchor_project_derived_program_ast(monkeypatch):
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_anchor_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    program_path = Path("tests/mocks/anchor-test/programs/anchor-test")
    result = generate_anchor_project_derived_program_ast(program_path)

    assert isinstance(result, dict)
    assert "sources" in result
    assert (
        result["sources"].get("tests/mocks/anchor-test/programs/anchor-test/src/lib.rs")
        is not None
    )


def test_generate_aggregate_program_ast(monkeypatch):
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_anchor_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    base_path = Path("tests/mocks/anchor-test-2/programs")
    result = generate_aggregate_program_ast(base_path)

    assert isinstance(result, dict)
    assert "sources" in result
    assert (
        result["sources"].get(
            "tests/mocks/anchor-test-2/programs/my-contracts/anchor-test-program-1/src/lib.rs"
        )
        is not None
    )
    assert (
        result["sources"].get(
            "tests/mocks/anchor-test-2/programs/my-contracts/anchor-test-program-2/src/lib.rs"
        )
        is not None
    )
