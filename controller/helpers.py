import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys


no_results_sarif = {
    "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
    "version": "2.1.0",
    "runs": [
        {
            "tool": {
                "driver": {
                    "name": "radar",
                    "informationUri": "https://github.com/auditware/radar",
                    "rules": [],
                }
            },
            "results": [],
        }
    ],
}


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
        "--templates-filename",
        type=str,
        required=False,
        help="Original filename when a single template file is provided",
    )
    parser.add_argument(
        "--ast",
        required=False,
        action="store_true",
        help="Copy generated AST alongside the report",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Path to the output directory (optional) (default - current folder)",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        required=False,
        help="Comma-separated severities to ignore in the scan (e.g. low,medium)",
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


def copy_to_docker_mount(
    radar_src_path: Path, api_dst_path: Path, path_type: str
) -> None:

    if not radar_src_path.exists():
        raise FileNotFoundError(f"No such {path_type}: {radar_src_path}")

    if api_dst_path.exists():
        if api_dst_path.is_dir():
            shutil.rmtree(api_dst_path)
        else:
            api_dst_path.unlink()

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


def print_write_outputs(
    results: list,
    ast: dict,
    write_ast: bool,
    path: Path,
    output_type: str,
    ignore_severities: str | None,
):
    container_output_file_path = Path(f"/radar_data/output.{output_type}")
    container_output_path_ast = Path("/radar_data/ast.json")

    if ignore_severities:
        ignored = set(
            s.strip().lower() for s in ignore_severities.replace(",", " ").split()
        )
    else:
        ignored = set()
    results = [
        finding for finding in results if finding["severity"].lower() not in ignored
    ]

    if len(results) == 0:
        print("[i] Radar completed successfully. No results found.")
        if output_type == "sarif":
            print("[i] Writing empty SARIF to indicate no results.")
            output_file = Path(container_output_file_path)
            with output_file.open("w") as outfile:
                json.dump(no_results_sarif, outfile, indent=4)
        sys.exit(0)

    for finding in results:
        print()
        locations = finding["locations"]
        locations_length = len(locations)
        if locations_length < 8:
            print(f"[ {finding['severity']} ] {finding['name']} found at:")
            for location in locations:
                print(f" * {location}")
        else:
            print(
                f"[ {finding['severity']} ] {finding['name']} found at {locations_length} locations, see output file for more details."
            )
        print()

    container_output_file_path.parent.mkdir(parents=True, exist_ok=True)

    if output_type == "sarif":
        write_sarif_output(container_output_file_path, results, path)
    elif output_type == "md":
        save_markdown_output(container_output_file_path, results)
    else:
        save_json_output(container_output_file_path, results)

    if write_ast:
        with open(container_output_path_ast, "w") as f:
            json.dump(ast, f, indent=4)

    print(
        f"[i] Radar completed successfully. {output_type} results were saved to disk."
    )


def convert_severity_to_sarif_level(severity: str) -> str:
    severity_mapping = {"High": "error", "Medium": "warning", "Low": "note"}
    sarif_level = severity_mapping.get(severity)
    if sarif_level is None:
        print("[e] Could not convert severity to SARIF level")
    return sarif_level


def convert_severity_to_sarif_security_severity(severity: str) -> str:
    security_severity_mapping = {"High": "8.0", "Medium": "5.0", "Low": "3.0"}
    sarif_security_severity = security_severity_mapping.get(severity)
    if sarif_security_severity is None:
        print("[e] Could not convert severity to SARIF security severity")
    return sarif_security_severity


def parse_location(location: str):
    file_path, line_info, column_info = location.split(":")
    start_line = int(line_info)
    start_column, end_column = map(int, column_info.split("-"))
    return file_path, start_line, start_column, end_column


def save_json_output(container_output_file_path: Path, findings: list):
    with open(container_output_file_path, "w") as f:
        json.dump(findings, f, indent=4)


def write_sarif_output(output_file_path: Path, findings: list, arg_path: Path):
    sarif_run_template = {
        "tool": {
            "driver": {
                "name": "radar",
                "informationUri": "https://github.com/auditware/radar",
                "rules": [],
            }
        },
        "artifacts": [],
        "results": [],
    }

    sarif_rule_template = {
        "id": "",
        "name": "",
        "shortDescription": {"text": ""},
        "fullDescription": {"text": ""},
        "help": {
            "text": "",
            "markdown": "",
        },
        "properties": {"precision": "", "security-severity": ""},
    }

    output_file = Path(output_file_path)

    if output_file.exists() and str(output_file).endswith(".sarif"):
        with output_file.open("r") as infile:
            try:
                sarif_json = json.load(infile)
                print("[i] Loaded from previous SARIF file")
            except json.JSONDecodeError:
                print("[w] Failed to decode existing SARIF file, creating a new one")
                sarif_json = {
                    "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
                    "version": "2.1.0",
                    "runs": [],
                }
    else:
        sarif_json = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "version": "2.1.0",
            "runs": [],
        }

    new_run = copy.deepcopy(sarif_run_template)

    for finding in findings:
        rule_id = finding["name"].replace(" ", "_")
        rule_exists = False

        for index, rule in enumerate(new_run["tool"]["driver"]["rules"]):
            if rule["id"] == rule_id:
                rule_exists = True
                rule_index = index
                break

        if not rule_exists:
            new_rule = copy.deepcopy(sarif_rule_template)
            new_rule["id"] = rule_id
            new_rule["name"] = finding["name"]
            new_rule["shortDescription"]["text"] = finding["name"]
            new_rule["fullDescription"]["text"] = finding["description"]
            new_rule["help"]["text"] = ""
            new_rule["help"]["markdown"] = ""
            new_rule["properties"]["precision"] = finding["certainty"].casefold()
            new_rule["properties"]["security-severity"] = (
                convert_severity_to_sarif_security_severity(finding["severity"])
            )

            new_run["tool"]["driver"]["rules"].append(new_rule)
            rule_index = len(new_run["tool"]["driver"]["rules"]) - 1

            for location in finding["locations"]:
                file_path, start_line, start_column, end_column = parse_location(
                    location
                )

                relative_file_path = str(Path(file_path).relative_to(arg_path))

                new_result = {
                    "ruleId": rule_id,
                    "ruleIndex": rule_index,
                    "level": convert_severity_to_sarif_level(finding["severity"]),
                    "message": {"text": finding["name"]},
                    "locations": [],
                }

                artifact_uri = f"file://{relative_file_path}"

                artifact_index = 0
                artifact_exists = False

                for existing_artifact_index, artifact in enumerate(
                    new_run["artifacts"]
                ):
                    if artifact["location"]["uri"] == artifact_uri:
                        artifact_index = existing_artifact_index
                        artifact_exists = True
                        break

                if not artifact_exists:
                    new_artifact = {"location": {"uri": artifact_uri}}
                    new_run["artifacts"].append(new_artifact)
                    artifact_index = len(new_run["artifacts"]) - 1

                new_result_location = {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": relative_file_path,
                            "index": artifact_index,
                        },
                        "region": {
                            "startLine": start_line,
                            "startColumn": start_column,
                            "endColumn": end_column,
                        },
                    }
                }
                new_result["locations"].append(new_result_location)
                new_run["results"].append(new_result)

    sarif_json["runs"].append(new_run)

    with output_file.open("w") as outfile:
        json.dump(sarif_json, outfile, indent=4)


def save_markdown_output(container_output_file_path: Path, findings: list):
    markdown = "# Radar Static Analysis Report\n\n"
    markdown += f"This report was generated on {datetime.now().strftime('%d.%m.%Y at %H:%M')}. The results are provided for informational purposes only and should not replace thorough audits or expert evaluations. Users are responsible for conducting their own assessments and ensuring accuracy before making decisions.\n\n"
    markdown += "## Alert Summary\n\n"
    markdown += "| Alert       | Severity    | Certainty   | Locations   |\n"
    markdown += "|-------------|-------------|-------------|-------------|\n"

    details = ""

    for finding in findings:
        name = finding["name"]
        severity = finding["severity"]
        certainty = finding["certainty"]
        locations = len(finding["locations"])
        md_name = name.replace(" ", "-").replace(",", "").replace(".", "").lower()

        markdown += (
            f"| [{name}](#{md_name}) | {severity} | {certainty} | {locations} |\n"
        )
        details += f"\n### {name}\n"
        details += f"**Severity:** {severity} | **Certainty:** {certainty}\n\n"
        details += f"{finding['description']}\n\n"
        details += "#### Locations\n"
        for location in finding["locations"]:
            details += f"- {location}\n"

        details += "---\n"

    markdown += "\n" + details

    with open(container_output_file_path, "w") as md_file:
        md_file.write(markdown)
