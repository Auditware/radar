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
            f"[e] Error: Contract path provided in argument {path} was not found. Did you configure the volume mount correctly?"
        )
        raise FileNotFoundError

    if path.is_file():
        return "file"
    if path.is_dir():
        return "folder"


def copy_to_docker_mount(path_type: str) -> None:
    src_path = Path("/contract") 
    dst_path = Path("/radar_data") / src_path.relative_to("/")

    if not src_path.exists():
        raise FileNotFoundError(f"No such {path_type}: {src_path}")

    shutil.rmtree(Path("/radar_data") / "contract")

    try:
        if path_type == "file":
            if src_path.is_symlink():
                os.symlink(os.readlink(src_path), dst_path)
            else:
                shutil.copy2(src_path, dst_path)

        elif path_type == "folder":
            shutil.copytree(
                src_path,
                dst_path,
                dirs_exist_ok=True,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    "*.tmp", "*cache*", "node_modules", "*.git", "target"
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
