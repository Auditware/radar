"""
Generate ast.json for Solidity mock files used in template tests.

Usage:
    cd api/
    poetry run python scripts/generate_mock_ast.py <path/to/contract.sol> <output/ast.json>

The output ast.json includes src_calculated (file:line:col_start-col_end) on each node,
enabling accurate line-level test assertions in test_templates.py.
"""

import sys
import json
from pathlib import Path


def byte_offset_to_line_col(source: str, byte_offset: int, length: int):
    """Convert a Solidity src byte offset + length to (line, col_start, col_end)."""
    lines = source.splitlines(keepends=True)
    current = 0
    for line_num, line in enumerate(lines, start=1):
        line_len = len(line.encode("utf-8"))
        if current + line_len > byte_offset:
            col_start = byte_offset - current + 1
            col_end = col_start + length - 1
            return line_num, col_start, col_end
        current += line_len
    return 1, 1, 1


def enrich_ast_with_src_calculated(node, source_content: str, file_path: str):
    """Recursively add src_calculated to every node that has a 'src' field."""
    if isinstance(node, dict):
        src = node.get("src")
        if src and isinstance(src, str) and ":" in src:
            parts = src.split(":")
            if len(parts) >= 2:
                try:
                    byte_offset = int(parts[0])
                    length = int(parts[1])
                    line, col_start, col_end = byte_offset_to_line_col(
                        source_content, byte_offset, length
                    )
                    node["src_calculated"] = f"{file_path}:{line}:{col_start}-{col_end}"
                except (ValueError, IndexError):
                    pass
        for value in node.values():
            enrich_ast_with_src_calculated(value, source_content, file_path)
    elif isinstance(node, list):
        for item in node:
            enrich_ast_with_src_calculated(item, source_content, file_path)


def generate_ast(sol_path: Path, output_path: Path):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.solidity_compiler import compile_solidity_file

    print(f"[i] Compiling {sol_path}...")
    result = compile_solidity_file(sol_path)

    source_content = sol_path.read_text()
    sources = result.get("sources", {})

    for file_key, file_data in sources.items():
        ast_node = file_data.get("ast", {})
        enrich_ast_with_src_calculated(ast_node, source_content, file_key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"[i] Written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_mock_ast.py <contract.sol> <output/ast.json>")
        sys.exit(1)

    generate_ast(Path(sys.argv[1]), Path(sys.argv[2]))
