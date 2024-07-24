import argparse
import json
import os
from pathlib import Path
import shutil


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="radar")
    parser.add_argument(
        "--path", type=str, required=False, help="Path to the contract on the host"
    )
    parser.add_argument(
        "--container-path",
        type=str,
        required=True,
        help="Specific source within the contract path (optional) (default - project root)",
    )
    parser.add_argument(
        "--templates",
        type=str,
        required=False,
        help="Path to the templates directory (optional) (default - builtin_templates folder)",
    )
    parser.add_argument(
        "--ast",
        required=False,
        action="store_true",
        help="Copy generated AST alongside the report",
    )
    return parser.parse_args()


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        error_msg = f"Set the {var_name} environment variable"
        raise EnvironmentError(error_msg)
    return value


def check_path(path: Path) -> str:
    if not path.exists():
        print(
            f"[e] Error: Contract path provided in argument {path} was not found. Did you configure the volume mount correctly?"
        )
        raise FileNotFoundError

    if path.is_file():
        return "file"
    if path.is_dir():
        return "folder"


def copy_to_docker_mount(radar_src_path: Path, api_dst_path: Path, path_type: str) -> None:

    if not radar_src_path.exists():
        raise FileNotFoundError(f"No such {path_type}: {radar_src_path}")

    if api_dst_path.exists():
        shutil.rmtree(api_dst_path)

    try:
        if path_type == "file":
            if radar_src_path.is_symlink():
                os.symlink(os.readlink(radar_src_path), api_dst_path)
            else:
                shutil.copy2(radar_src_path, api_dst_path)

        elif path_type == "folder":
            shutil.copytree(
                radar_src_path,
                api_dst_path,
                dirs_exist_ok=True,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    "*.tmp", "*cache*", "node_modules", "*.git", "target", ".DS_Store"
                ),
            )

        else:
            raise ValueError("Invalid path_type: Must be 'file' or 'folder'")

        print(f"[i] Successfully copied {path_type}")
    except Exception as e:
        raise Exception(f"[e] Failed to copy {path_type} to volume: {str(e)}")


def localize_results(results, local_path):
    for index, result in enumerate(results):
        result_locations = result.get("locations")
        localized_results = []
        for location in result_locations:
            container_path, location_src = location.split(":", 1)
            container_path_parts = Path(container_path).parts
            localized_path = Path(local_path, *container_path_parts[3:])
            localized_location = f"{localized_path}:{location_src}"
            localized_results.append(localized_location)
        results[index]["locations"] = localized_results
    return results


def print_write_outputs(results: list, ast: dict, write_ast: bool):
    container_output_path_json = Path("/radar_data/output.json")
    container_output_path_ast = Path("/radar_data/ast.json")

    if len(results) == 0:
        print("[i] Radar completed successfully. No results found.")
        return

    print(
        f"[i] Radar completed successfully. Results (also saved to output.json{' & ast.json' if write_ast else ''}):"
    )
    print(json.dumps(results, indent=4).replace('\\"', ''))

    container_output_path_json.parent.mkdir(parents=True, exist_ok=True)

    with open(container_output_path_json, "w") as f:
        json.dump(results, f, indent=4)

    if write_ast:
        with open(container_output_path_ast, "w") as f:
            json.dump(ast, f, indent=4)
