import json
from pathlib import Path
import sys
import re
from typing import Any


import logging

import toml

logger = logging.getLogger(__name__)

# A Rust lifetime (`'info`) vs a char literal (`'a'`): the lifetime's identifier
# is not immediately followed by a closing quote. Compiled once and matched at an
# offset so masking never slices the source tail per apostrophe.
_LIFETIME_RE = re.compile(r"'[A-Za-z_][A-Za-z0-9_]*(?!')")


def generate_ast_for_solidity_file(source_file_path: Path, remappings: list = None, base_path: Path = None) -> dict:
    from utils.solidity_compiler import compile_solidity_file
    
    try:
        ast_output = compile_solidity_file(source_file_path, remappings=remappings, base_path=base_path)
        return {"ast": ast_output, "metadata": {}}
    except Exception as e:
        logger.error(f"Failed to generate Solidity AST: {e}")
        raise


def parse_toml_keys(toml_path: Path, keys: list) -> list:
    toml_data = toml.load(toml_path)
    results = []
    for key in keys:
        parts = key.split(".")
        value = toml_data
        try:
            for part in parts:
                value = value[part]
            results.append(value)
        except KeyError:
            results.append(None)
            print(f"[w] Key '{key}' not found in {toml_path}")
    return results


def generate_ast_for_rust_file(
    source_file_path: Path, package_name: str = None, package_version: str = None
) -> dict:
    rust_code = source_file_path.read_text()

    try:
        # Ensure proper import of rust_syn.so (copied at build time)
        path_to_rust_syn_so = "/api/utils"
        if path_to_rust_syn_so not in sys.path:
            sys.path.append(path_to_rust_syn_so)
        import rust_syn  # type: ignore

        ast_data = rust_syn.parse_rust_to_ast(rust_code)
        ast_data = json.loads(ast_data)

        enriched_ast = enrich_ast_with_source_lines(
            ast_data.get("items"), rust_code, source_file_path
        )

        source_sepcific_metadata = {}
        if package_name or package_version:
            source_sepcific_metadata["program_info"] = {
                "name": package_name,
                "version": package_version,
            }

    except Exception as e:
        raise e

    return {"ast": enriched_ast, "metadata": source_sepcific_metadata}


def enrich_ast_with_source_lines(
    ast_items: dict, rust_code: str, source_file_path: Path
) -> dict:
    def mask_comments_and_strings(code: str) -> str:
        """Blank out comments and string literals, preserving every offset.

        Identifier positions are found by scanning the source text, so prose
        that happens to contain an identifier - a doc comment naming the very
        account it documents, say - otherwise contributes phantom positions
        and pushes every later node onto the wrong line.
        """
        out = list(code)
        i, n = 0, len(code)
        while i < n:
            if code.startswith("//", i):
                while i < n and code[i] != "\n":
                    out[i] = " "
                    i += 1
            elif code.startswith("/*", i):
                depth = 1
                out[i] = out[i + 1] = " "
                i += 2
                while i < n and depth:
                    if code.startswith("/*", i):
                        depth += 1
                        out[i] = out[i + 1] = " "
                        i += 2
                    elif code.startswith("*/", i):
                        depth -= 1
                        out[i] = out[i + 1] = " "
                        i += 2
                    else:
                        if code[i] != "\n":
                            out[i] = " "
                        i += 1
            elif code[i] == "'":
                # A lifetime shares its opening quote with a char literal, and
                # has no closing one. Match at position i rather than slicing
                # code[i:], which would copy the file tail on every apostrophe
                # (lifetimes are dense in Anchor code) and make masking O(n^2).
                if _LIFETIME_RE.match(code, i):
                    i += 1
                    continue
                i += 1
                while i < n and code[i] != "'":
                    if code[i] == "\\":
                        out[i] = " "
                        i += 1
                    if i < n:
                        if code[i] != "\n":
                            out[i] = " "
                        i += 1
                i += 1
            elif code[i] == '"':
                i += 1
                while i < n and code[i] != '"':
                    if code[i] == "\\":
                        out[i] = " "
                        i += 1
                    if i < n:
                        if code[i] != "\n":
                            out[i] = " "
                        i += 1
                i += 1
            else:
                i += 1
        return "".join(out)

    def find_ident_positions(code: str, ident: str) -> list[dict]:
        positions = []
        pattern = re.compile(r"\b" + re.escape(ident) + r"\b")
        for match in pattern.finditer(code):
            start_pos = match.start()
            line_num = code.count("\n", 0, start_pos) + 1
            line_start = code.rfind("\n", 0, start_pos) + 1
            end_pos = match.end()
            start_col = start_pos - line_start + 1
            end_col = end_pos - line_start + 1
            positions.append(
                {
                    "file": str(source_file_path),
                    "line": line_num,
                    "start_col": start_col,
                    "end_col": end_col,
                }
            )
        return positions

    def source_ordered_items(node: dict) -> list:
        """Yield a node's entries in the order they appear in Rust source.

        Positions are handed out by walking the tree and consuming successive
        textual occurrences, so the walk has to follow source order. The parser's
        JSON does not: a struct field carries `ident` before `attrs`, while in
        source the `#[account(...)]` attribute is written above the field name,
        and a `where` clause is nested under `generics` although it is written
        after the parameter list and return type. Visiting keys in declaration
        order therefore assigned those nodes each other's positions.

        Keys not listed keep their original relative order (the sort is stable),
        so unknown shapes behave exactly as before.
        """
        rank = {
            "attrs": 0,          # attributes precede everything they decorate
            "vis": 1,
            "defaultness": 2, "constness": 2, "asyncness": 2,
            "unsafety": 2, "abi": 2, "mutability": 2,
            "ident": 3,
            "generics": 4,       # <T> parameters (where-clause split out below)
            "inputs": 5, "fields": 5, "variants": 5, "args": 5,
            "self_ty": 5, "trait": 5, "ty": 5, "colon_token": 5,
            "output": 6,
            "where_clause": 7,   # written after the parameter list/return type
            "block": 8, "stmts": 8, "body": 8, "expr": 8,
        }
        # A where-clause lives under `generics` but is written last, so it is
        # visited separately after `inputs`/`output`. The generics entry keeps
        # the original object (never a copy, so enrichment still writes through
        # to the real tree) and the walk is told to skip that one key.
        deferred = []
        rebuilt = []
        for key, value in node.items():
            if key == "generics" and isinstance(value, dict) and "where_clause" in value:
                rebuilt.append((key, value, frozenset({"where_clause"})))
                deferred.append(("where_clause", value["where_clause"], frozenset()))
            else:
                rebuilt.append((key, value, frozenset()))
        rebuilt.extend(deferred)

        return sorted(rebuilt, key=lambda kv: rank.get(kv[0], 5))

    def enrich_node(
        node: Any,
        scanned_idents: dict[str, list[dict]],
        consumed: dict[str, int],
        skip_keys: frozenset = frozenset(),
    ) -> None:
        if isinstance(node, dict):
            items = source_ordered_items(node)
            for key, value, child_skip in items:
                if key in skip_keys:
                    continue
                if isinstance(value, dict):
                    enrich_node(value, scanned_idents, consumed, child_skip)
                elif isinstance(value, list):
                    for item in value:
                        enrich_node(item, scanned_idents, consumed)
                elif key in ("ident", "method", "int"):
                    ident = value
                    if key == "method":
                        node["ident"] = ident
                    if key == "int":
                        node["ident"] = str(node["int"])
                    if ident not in scanned_idents:
                        scanned_idents[ident] = find_ident_positions(
                            masked_code, ident
                        )
                        consumed[ident] = 0

                    positions = scanned_idents[ident]
                    if positions:
                        # Hand each node the next unclaimed occurrence. The
                        # walk follows source order, so the nth node bearing an
                        # identifier is the nth place it is written. Assigning
                        # positions[0] every time - which is what the previous
                        # membership test did, since it compared against the
                        # node's own absent "src" - collapsed every repeat of
                        # an identifier onto its first appearance in the file.
                        index = min(consumed[ident], len(positions) - 1)
                        node["src"] = positions[index]
                        consumed[ident] = index + 1

        elif isinstance(node, list):
            for item in node:
                enrich_node(item, scanned_idents, consumed)

    masked_code = mask_comments_and_strings(rust_code)
    scanned_idents = {}
    consumed = {}
    enrich_node(ast_items, scanned_idents, consumed)
    return ast_items


def find_anchor_program_paths(source_file_path, workspace_members):
    program_paths = []

    for member in workspace_members:
        full_path = Path(source_file_path) / member
        if "*" in member:
            program_paths.extend(
                [p for p in full_path.parent.glob(full_path.name) if p.is_dir()]
            )
        else:
            if full_path.is_dir():
                program_paths.append(full_path)
            else:
                logger.warn(
                    f"Program directory listed on Cargo.toml's workspace.members does not exist: {full_path}"
                )

    return program_paths


def generate_ast_for_rust_program(source_file_path: Path) -> dict:
    cargo_toml_path = source_file_path / "Cargo.toml"
    package_name, package_version = parse_toml_keys(
        cargo_toml_path, ["package.name", "package.version"]
    )
    directory = cargo_toml_path.parent
    rs_files = list(directory.rglob("*.rs"))

    radar_ast = {"sources": {}, "metadata": {}}
    for rs_file in rs_files:
        file_ast = generate_ast_for_rust_file(rs_file, package_name, package_version)
        radar_ast["sources"][str(rs_file)] = file_ast

    sorted_sources = dict(sorted(radar_ast["sources"].items()))
    radar_ast["sources"] = sorted_sources

    return radar_ast


def generate_anchor_project_derived_program_ast(program_path: Path) -> dict:
    cargo_toml_path = program_path / "Cargo.toml"
    package_name, package_version = parse_toml_keys(
        cargo_toml_path, ["package.name", "package.version"]
    )
    rs_files = list(program_path.rglob("*.rs"))

    program_ast = {"sources": {}, "metadata": {}}

    for rs_file in rs_files:
        file_ast = generate_ast_for_rust_file(rs_file, package_name, package_version)
        program_ast["sources"][str(rs_file)] = file_ast
        program_ast["metadata"][str(rs_file)] = {
            "package_name": package_name,
            "package_version": package_version,
            "cargo_toml_path": str(cargo_toml_path),
        }

    return program_ast


def generate_ast_for_anchor_project(source_path: Path) -> dict:
    anchor_toml_path = source_path / "Anchor.toml"
    anchor_version, solana_version = parse_toml_keys(
        anchor_toml_path, ["anchor_version", "solana_version"]
    )
    anchor_toml_path = str(anchor_toml_path)

    cargo_toml_path = source_path / "Cargo.toml"
    workspace_members = parse_toml_keys(cargo_toml_path, ["workspace.members"])

    # extract array from array
    workspace_members = workspace_members[0]
    programs = find_anchor_program_paths(source_path, workspace_members)

    project_ast = {
        "metadata": {
            key: value
            for key, value in [
                ("anchor_version", anchor_version),
                ("solana_version", solana_version),
                ("anchor_toml_path", anchor_toml_path),
            ]
            if value is not None
        },
        "sources": {},
    }

    for program_path in programs:
        program_ast = generate_anchor_project_derived_program_ast(program_path)
        project_ast["sources"].update(program_ast["sources"])

    sorted_sources = dict(sorted(project_ast["sources"].items()))
    project_ast["sources"] = sorted_sources

    return project_ast


def generate_aggregate_program_ast(base_path: Path) -> dict | None:
    project_ast = {"sources": {}, "metadata": {}}
    found_cargo_toml = False

    def process_directory(directory):
        nonlocal found_cargo_toml
        for subdir in directory.iterdir():
            if subdir.is_dir():
                if (subdir / "Cargo.toml").exists():
                    found_cargo_toml = True
                    program_ast = generate_ast_for_rust_program(subdir)
                    for file_path, ast in program_ast["sources"].items():
                        project_ast["sources"][file_path] = ast
                process_directory(subdir)

    process_directory(base_path)

    if not found_cargo_toml:
        return None

    sorted_sources = dict(sorted(project_ast["sources"].items()))
    project_ast["sources"] = sorted_sources

    return project_ast