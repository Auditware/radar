import argparse
import json
import os
from pathlib import Path
import shutil


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="radar")
    parser.add_argument(
        "--path", type=str, required=False, help="Path to the contract source"
    )
    parser.add_argument(
        "--container-path",
        type=str,
        required=True,
        help="Path to the contract source on the docker container",
    )
    parser.add_argument(
        "--templates", type=str, required=False, help="Path to custom templates folder"
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
            "[e] Error: Contract path provided in argument was not found. Did you configure the volume mount correctly?"
        )
        raise FileNotFoundError

    if path.is_file():
        return "file"
    if path.is_dir():
        return "folder"


def copy_to_docker_mount(src_path: Path, path_type: str) -> None:
    dst_path = Path("/radar_data") / src_path.relative_to("/")
    if dst_path.exists() and dst_path.is_dir():
        shutil.rmtree(dst_path)

    try:
        if path_type == "file":
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dst_path)
        elif path_type == "folder":
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        print(f"[i] Successfully copied {path_type} to {dst_path}")
    except Exception as e:
        raise Exception(f"[e] Failed to copy contract {path_type} to volume: {str(e)}")


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


def print_write_outputs(results: list, container_output_path: Path):
    if len(results) == 0:
        print("[i] Radar completed successfully. No results found.")
        return
    print("[i] Radar completed successfully. Results (also saved to output.json):")
    print(json.dumps(results, indent=4))

    container_output_path.parent.mkdir(parents=True, exist_ok=True)
    if container_output_path.exists():
        container_output_path.unlink()

    with open(container_output_path, "w") as f:
        json.dump(results, f, indent=4)
