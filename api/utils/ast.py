import json
from pathlib import Path
import sys
import re
from typing import Any


import logging

import toml

logger = logging.getLogger(__name__)


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
            print(f"Key '{key}' not found in {toml_path}")
    return results


def generate_ast_for_anchor_file(
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

    def enrich_node(node: Any, scanned_idents: dict[str, list[dict]]) -> None:
        if isinstance(node, dict):
            items = list(node.items())
            for key, value in items:
                if isinstance(value, dict):
                    enrich_node(value, scanned_idents)
                elif isinstance(value, list):
                    for item in value:
                        enrich_node(item, scanned_idents)
                elif key == "ident":
                    ident = value
                    if ident not in scanned_idents:
                        positions = find_ident_positions(rust_code, ident)
                        if positions:
                            node["src"] = positions[0]
                            scanned_idents[ident] = positions
                    else:
                        for pos in scanned_idents[ident]:
                            if pos not in node.get("src", []):
                                node["src"] = pos
                                break
        elif isinstance(node, list):
            for item in node:
                enrich_node(item, scanned_idents)

    scanned_idents = {}
    enrich_node(ast_items, scanned_idents)
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


def generate_anchor_program_ast(source_file_path: Path) -> dict:
    cargo_toml_path = source_file_path / "Cargo.toml"
    package_name, package_version = parse_toml_keys(
        cargo_toml_path, ["package.name", "package.version"]
    )
    directory = cargo_toml_path.parent
    rs_files = list(directory.rglob("*.rs"))

    radar_ast = {"sources": {}, "metadata": {}}
    for rs_file in rs_files:
        file_ast = generate_ast_for_anchor_file(rs_file, package_name, package_version)
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
        file_ast = generate_ast_for_anchor_file(rs_file, package_name, package_version)
        program_ast["sources"][str(rs_file)] = file_ast
        program_ast["metadata"][str(rs_file)] = {
            "package_name": package_name,
            "package_version": package_version,
            "cargo_toml_path": str(cargo_toml_path),
        }

    return program_ast


def generate_anchor_project_ast(source_path: Path) -> dict:
    anchor_toml_path = source_path / "Anchor.toml"
    anchor_version, solana_version = parse_toml_keys(
        anchor_toml_path, ["anchor_version", "solana_version"]
    )

    cargo_toml_path = source_path / "Cargo.toml"
    workspace_members = parse_toml_keys(cargo_toml_path, ["workspace.members"])

    # extract array from array
    workspace_members = workspace_members[0]
    programs = find_anchor_program_paths(source_path, workspace_members)

    project_ast = {
        "metadata": {
            "anchor_version": anchor_version,
            "solana_version": solana_version,
            "anchor_toml_path": str(anchor_toml_path),
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
                    program_ast = generate_anchor_program_ast(subdir)
                    for file_path, ast in program_ast["sources"].items():
                        project_ast["sources"][file_path] = ast
                process_directory(subdir)

    process_directory(base_path)

    if not found_cargo_toml:
        return None

    sorted_sources = dict(sorted(project_ast["sources"].items()))
    project_ast["sources"] = sorted_sources

    return project_ast
