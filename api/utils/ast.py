import json
from pathlib import Path
import sys
import re
from typing import Any


import logging

logger = logging.getLogger(__name__)


def generateASTForAnchorFile(source_file_path: Path) -> dict:
    rust_code = source_file_path.read_text()

    try:
        # Ensure proper import of rust_syn.so (copied at build time)
        path_to_rust_syn_so = "/api/utils"
        if path_to_rust_syn_so not in sys.path:
            sys.path.append(path_to_rust_syn_so)
        import rust_syn  # type: ignore

        ast_data = rust_syn.parse_rust_to_ast(rust_code)
        ast_data = json.loads(ast_data)

        enriched_ast = enrich_ast_with_source_lines(ast_data.get("items"), rust_code)

        radar_ast = {"sources": {}, "metadata": {}}
        radar_ast["sources"][str(source_file_path)] = {
            "ast": enriched_ast,
            "metadata": {},
        }
    except Exception as e:
        raise e

    return radar_ast


def enrich_ast_with_source_lines(ast_items: dict, rust_code: str) -> dict:
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
                {"line": line_num, "start_col": start_col, "end_col": end_col}
            )
        return positions

    def enrich_node(node: Any, scanned_idents: dict[str, list[dict]]) -> None:
        if isinstance(node, dict):
            items = list(
                node.items()
            )
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
