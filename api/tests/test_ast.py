from pathlib import Path
from utils.ast import (
    generate_aggregate_program_ast,
    generate_ast_for_anchor_project,
    generate_anchor_project_derived_program_ast,
)

mock_rust_syn_ast = {
    "ast": {"items": [{"type": "function", "name": "main", "src": "fn main() {}"}]},
    "metadata": {"program_info": {"name": "test_program", "version": "0.1.0"}},
}


def test_generate_ast_for_anchor_project(monkeypatch):
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_rust_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    source_path = Path("tests/mocks/anchor-test")
    result = generate_ast_for_anchor_project(source_path)

    assert isinstance(result, dict)
    assert "sources" in result
    assert (
        result["metadata"]["anchor_toml_path"] == "tests/mocks/anchor-test/Anchor.toml"
    )


def test_generate_anchor_project_derived_program_ast(monkeypatch):
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_rust_file",
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
        "utils.ast.generate_ast_for_rust_file",
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


def test_aggregate_ast_accepts_a_crate_at_the_scanned_root(monkeypatch, tmp_path):
    """A native Solana crate is usually Cargo.toml + src/ at the root of the path
    given to radar. Only subdirectories were searched, so such a program was
    rejected with 'No Cargo.toml files found in any subdirectories'."""
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_rust_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "native-program"\nversion = "0.1.0"\n'
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lib.rs").write_text("fn main() {}")

    result = generate_aggregate_program_ast(tmp_path)

    assert result is not None
    assert result["sources"].get(str(tmp_path / "src" / "lib.rs")) is not None


def test_aggregate_ast_leaves_a_pure_workspace_root_to_its_members(monkeypatch, tmp_path):
    """A [workspace] manifest declares no package and owns no sources, so it must
    not be walked as a program in its own right."""
    monkeypatch.setattr(
        "utils.ast.generate_ast_for_rust_file",
        lambda *args, **kwargs: mock_rust_syn_ast,
    )
    (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["programs/one"]\n')
    member = tmp_path / "programs" / "one"
    member.mkdir(parents=True)
    (member / "Cargo.toml").write_text('[package]\nname = "one"\nversion = "0.1.0"\n')
    (member / "src").mkdir()
    (member / "src" / "lib.rs").write_text("fn one() {}")

    result = generate_aggregate_program_ast(tmp_path)

    assert result is not None
    assert result["sources"].get(str(member / "src" / "lib.rs")) is not None
