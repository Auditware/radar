"""Generate the ast.json fixtures the template accuracy suite reads.

`tests/mocks/<name>/{bad,good}/ast.json` is gitignored, so on a clean checkout
`test_template_accuracy` collects nothing. This walks every mock and writes the
fixture with the right parser:

    Rust (.rs)      -> {"ast": <enriched syn items>}  (needs rust_syn)
    Solidity (.sol) -> solc compile result             (needs solc/solc-select)

By default only *missing* fixtures are generated, so an existing fixture (and
the expected-line metadata recorded against it) is never silently rewritten.
Pass --force to regenerate everything.

    cd api/ && poetry run python scripts/generate_fixtures.py [--force] [name ...]
"""

import argparse
import json
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "tests"
MOCKS = TESTS / "mocks"


def _rust_ast(sources):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.ast import generate_ast_for_rust_file

    items = []
    for src in sources:
        items.extend(generate_ast_for_rust_file(src)["ast"])
    return {"ast": items}


def _solidity_ast(sol_path):
    # Reuse the existing enrichment used by the Solidity accuracy fixtures.
    from generate_mock_ast import enrich_ast_with_src_calculated
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.solidity_compiler import compile_solidity_file

    result = compile_solidity_file(sol_path)
    source_content = sol_path.read_text()
    for file_key, file_data in result.get("sources", {}).items():
        enrich_ast_with_src_calculated(file_data.get("ast", {}), source_content, file_key)
    return result


def _solidity_project_ast(sol_paths, base_path: Path):
    """Compile a multi-file Solidity mock as one unit, rooted at the variant dir.

    A single-file mock is compiled with its absolute path as the source unit
    name, which is fine for rules that only look at nodes. Rules that key on
    *import paths* (duplicate_imports matches `absolutePath` against `^lib/…`)
    can only ever fire on the relative, project-rooted source unit names solc
    produces for a real Foundry tree - which is what api/views.py passes at scan
    time via base_path. Mirroring that here lets such a mock be a faithful
    miniature of the layout the rule targets, instead of being unfixturable.

    Only reached when a variant dir holds more than one .sol file, so existing
    single-file mocks keep their absolute source keys untouched.
    """
    from generate_mock_ast import enrich_ast_with_src_calculated
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.solidity_compiler import compile_solidity_files

    result = compile_solidity_files(list(sol_paths), base_path=base_path)
    for file_key, file_data in result.get("sources", {}).items():
        source_file = base_path / file_key
        if not source_file.is_file():
            continue
        enrich_ast_with_src_calculated(
            file_data.get("ast", {}), source_file.read_text(), file_key
        )
    return result


def generate_variant(variant_dir: Path, force: bool):
    out = variant_dir / "ast.json"
    if out.exists() and not force:
        return "skip (exists)"

    rs = sorted(variant_dir.rglob("*.rs"))
    sol = sorted(variant_dir.rglob("*.sol"))
    try:
        if rs:
            data = _rust_ast(rs)
        elif len(sol) > 1:
            data = _solidity_project_ast(sol, variant_dir)
        elif sol:
            data = _solidity_ast(sol[0])
        else:
            return "skip (no sources)"
    except Exception as exc:  # missing toolchain, compile error, ...
        return f"ERROR: {exc}"

    out.write_text(json.dumps(data))
    return "written"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", help="mock names to (re)generate; default all")
    parser.add_argument("--force", action="store_true", help="regenerate existing fixtures too")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))  # for generate_mock_ast import

    names = args.names or sorted(p.name for p in MOCKS.iterdir() if p.is_dir())
    written = errors = 0
    for name in names:
        for variant in ("bad", "good"):
            vdir = MOCKS / name / variant
            if not vdir.is_dir():
                continue
            status = generate_variant(vdir, args.force)
            if status == "written":
                written += 1
            elif status.startswith("ERROR"):
                errors += 1
                print(f"[e] {name}/{variant}: {status}")
    print(f"[i] {written} fixture(s) written, {errors} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
