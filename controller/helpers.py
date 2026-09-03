import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Optional


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


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def meets_fail_threshold(severity: str, fail_on: str) -> bool:
    """True if a finding of `severity` should make radar exit non-zero.

    A finding gates the build when it is at least as severe as `fail_on`.
    `fail_on == "none"` never gates. Unknown severities are treated as the
    least severe so an unrecognised label never silently fails a build.
    """
    if not fail_on or fail_on.lower() == "none":
        return False
    threshold = SEVERITY_ORDER.get(fail_on.lower(), max(SEVERITY_ORDER.values()))
    rank = SEVERITY_ORDER.get(severity.lower(), max(SEVERITY_ORDER.values()))
    return rank <= threshold


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
    parser.add_argument(
        "--fail-on",
        type=str,
        required=False,
        default="low",
        choices=["critical", "high", "medium", "low", "none"],
        help=(
            "Minimum severity that makes radar exit non-zero for CI gating: "
            "any reported finding at or above this severity yields exit 1. "
            "'none' never fails on findings. Operational errors always exit 2. "
            "(default: low - fail on any finding)"
        ),
    )
    parser.add_argument(
        "--debug",
        required=False,
        action="store_true",
        help="Enable debug output including AST information",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        required=False,
        help="Path (in-container) to a baseline file; findings it lists are not reported or gated",
    )
    parser.add_argument(
        "--write-baseline",
        required=False,
        action="store_true",
        help="Snapshot current findings as the baseline instead of reporting/gating",
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

    # A scoped source nests under the mount (/radar_data/contract/src/lib.rs), so the
    # intermediate directories will not exist on the first copy.
    api_dst_path.parent.mkdir(parents=True, exist_ok=True)

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


def _relativize(file_path: str, root: Optional[Path]) -> str:
    """Best-effort project-relative path so baselines are portable across
    machines and container/host path differences."""
    if root is None:
        return file_path
    try:
        return str(Path(file_path).relative_to(root))
    except ValueError:
        return file_path


def finding_fingerprints(finding: dict, root: Optional[Path]):
    """Stable identity for each location of a finding: (rule, rel-file, line:cols).

    Location-based, so it survives across runs but not across large line moves -
    a deliberate simplicity trade-off for a first baseline; inline suppression
    covers the churny cases.
    """
    name = finding.get("name", "")
    prints = []
    for location in finding.get("locations", []):
        try:
            file_path, start_line, start_column, end_column = parse_location(location)
            rel = _relativize(file_path, root)
            prints.append(f"{name}::{rel}:{start_line}:{start_column}-{end_column}")
        except Exception:
            prints.append(f"{name}::{location}")
    return prints


def load_baseline(baseline_path: Path):
    """Read a baseline file into a set of fingerprints. Missing/invalid → empty."""
    try:
        data = json.loads(Path(baseline_path).read_text())
    except (OSError, json.JSONDecodeError):
        return set()
    if isinstance(data, dict):
        data = data.get("fingerprints", [])
    return set(data) if isinstance(data, list) else set()


def apply_baseline(results: list, baseline: set, root: Optional[Path]) -> list:
    """Drop locations already in the baseline; drop findings left with none."""
    surviving = []
    for finding in results:
        kept = []
        for location, fp in zip(
            finding.get("locations", []), finding_fingerprints(finding, root)
        ):
            if fp not in baseline:
                kept.append(location)
        if kept:
            new_finding = dict(finding)
            new_finding["locations"] = kept
            surviving.append(new_finding)
    return surviving


def location_sort_key(location: str):
    """Order locations by file, then line, then column, for stable output.

    Falls back to the raw string when a location does not parse, so ordering
    never throws on an unexpected shape.
    """
    try:
        file_path, start_line, start_column, _ = parse_location(location)
        return (file_path, start_line, start_column, location)
    except Exception:
        return (location, 0, 0, location)


def print_write_outputs(
    results: list,
    ast: dict,
    write_ast: bool,
    path: Path,
    output_type: str,
    ignore_severities: str | None,
    debug: bool = False,
    fail_on: str = "low",
    errors: list | None = None,
    baseline_path: str | None = None,
    write_baseline: bool = False,
):
    container_output_file_path = Path(f"/radar_data/output.{output_type}")
    container_output_path_ast = Path("/radar_data/ast.json")
    container_baseline_path = Path("/radar_data/baseline.json")
    errors = errors or []

    if ignore_severities:
        ignored = set(
            s.strip().lower() for s in ignore_severities.replace(",", " ").split()
        )
    else:
        ignored = set()
    
    # Filter by severity
    results = [
        finding for finding in results if finding["severity"].lower() not in ignored
    ]
    
    # Filter by certainty if "uncertain" is specified
    if "uncertain" in ignored:
        results = [
            finding for finding in results 
            if finding.get("certainty", "").lower() == "high"
        ]
    
    # Filter out findings with no locations (no actual issues found)
    results = [
        finding for finding in results
        if finding.get("locations") and len(finding["locations"]) > 0
    ]

    # Deduplicate repeated locations within each finding, preserving order.
    # Findings are aggregated per template with no dedup upstream, so the same
    # location can appear more than once; duplicates inflate counts and make
    # baseline diffs noisy.
    for finding in results:
        seen = set()
        deduped = []
        for location in finding["locations"]:
            if location not in seen:
                seen.add(location)
                deduped.append(location)
        finding["locations"] = sorted(deduped, key=location_sort_key)

    # Baseline handling. --write-baseline snapshots the current findings (after
    # --ignore filtering) so a team can accept everything present today and have
    # CI fail only on new findings; a subsequent run with --baseline filters
    # those known findings out before gating.
    if write_baseline:
        fingerprints = sorted(
            fp for finding in results for fp in finding_fingerprints(finding, path)
        )
        container_baseline_path.write_text(
            json.dumps({"fingerprints": fingerprints}, indent=2)
        )
        print(
            f"[i] Wrote baseline with {len(fingerprints)} finding(s). Future runs "
            f"with --baseline will not fail on these."
        )
        sys.exit(0)

    if baseline_path:
        baseline = load_baseline(baseline_path)
        before = sum(len(f.get("locations", [])) for f in results)
        results = apply_baseline(results, baseline, path)
        after = sum(len(f.get("locations", [])) for f in results)
        if before != after:
            print(f"[i] Baseline suppressed {before - after} known finding(s).")

    # Remove debug field from results if not in debug mode
    if not debug:
        for finding in results:
            finding.pop("debug", None)

    if ast and "sources" in ast:
        file_count = len(ast["sources"])
        filenames = [Path(file_path).name for file_path in ast["sources"].keys()]
        filenames_str = ",".join(filenames)
        print(
            f"[i] Scanned {file_count} file{'s' if file_count != 1 else ''} ({filenames_str})"
        )

        if debug:
            for i, result in enumerate(results):
                if "debug" in result:
                    print()
                    print(
                        f"[d] Debug output from template \"{result.get('name', 'Unknown')}\""
                    )
                    for i in range(0, len(result["debug"])):
                        print(result['debug'][i])

    if errors:
        print(
            f"[e] {len(errors)} template(s) failed to run; their findings are "
            f"not included in this report:"
        )
        for err in errors:
            print(f"    - {err.get('name', 'unknown')}: {err.get('error', 'unknown error')}")

    if len(results) == 0:
        # A clean scan still owes --output the file it promised. The CLI copies this
        # path out of the container and reports "Results written to ..." either way,
        # so writing nothing left the caller with a success message and no artefact.
        container_output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file = Path(container_output_file_path)
        if output_type == "sarif":
            print("[i] Writing empty SARIF to indicate no results.")
            with open(output_file, "w") as outfile:
                json.dump(no_results_sarif, outfile, indent=4)
        elif output_type == "md":
            with open(output_file, "w") as outfile:
                outfile.write("# radar\n\nNo results found.\n")
        else:
            with open(output_file, "w") as outfile:
                json.dump([], outfile, indent=4)

        if write_ast:
            with open(container_output_path_ast, "w") as f:
                json.dump(ast, f, indent=4)

        if errors:
            # A scan where templates errored out is not a clean scan, even with
            # no findings: exit 2 so CI does not read a partial run as "clean".
            print("[e] radar completed with template errors and no findings.")
            sys.exit(2)

        print("[i] radar completed successfully. No results found.")
        sys.exit(0)

    # Stable ordering: severity first, then finding name, so two scans of the
    # same tree emit findings in the same order (needed for baseline diffs).
    results = sorted(
        results,
        key=lambda x: (SEVERITY_ORDER.get(x["severity"].lower(), 4), x.get("name", "")),
    )
    
    color_map = {
        "Critical": "\033[38;2;139;0;0m",  # Dark red (RGB)
        "High": "\033[91m",  # Red
        "Medium": "\033[94m",  # Blue
        "Low": "\033[92m",  # Green
    }
    reset_color = "\033[0m"  # Reset to default color

    for finding in results:
        locations = finding["locations"]
        locations_length = len(locations)
        severity = finding["severity"]
        color = color_map.get(severity, "")

        if locations_length != 0:
            print()
            if locations_length < 20:
                print(f"[ {color}{severity}{reset_color} ] {finding['name']} found at:")
                for location in locations:
                    print(f" * {location}")
            else:
                print(
                    f"[ {color}{severity}{reset_color} ] {finding['name']} found at {locations_length} locations, see output file for more details."
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
        f"[i] radar completed successfully. {output_type} results were saved to disk."
    )

    # CI gating: exit non-zero when any reported finding is at or above the
    # fail-on threshold. radar historically exited 0 on findings, which
    # silently broke every exit-code-based gate (the shipped pre-commit hook
    # included). Operational errors take precedence and exit 2.
    if errors:
        print("[e] radar completed with template errors - exiting 2.")
        sys.exit(2)

    gating = [f for f in results if meets_fail_threshold(f["severity"], fail_on)]
    if gating:
        gating_count = sum(len(f["locations"]) for f in gating)
        print(
            f"[i] {gating_count} finding(s) at or above severity '{fail_on}' "
            f"- exiting 1 for CI gating (override with --fail-on)."
        )
        sys.exit(1)
    sys.exit(0)


def convert_severity_to_sarif_level(severity: str) -> str:
    severity_mapping = {
        "Critical": "error",
        "High": "error",
        "Medium": "warning",
        "Low": "warning",
    }  # 'note' sometimes is being hidden by sarif supported tools
    sarif_level = severity_mapping.get(severity)
    if sarif_level is None:
        print("[e] Could not convert severity to SARIF level")
    return sarif_level


def convert_severity_to_sarif_security_severity(severity: str) -> str:
    security_severity_mapping = {"Critical": "9.0", "High": "8.0", "Medium": "5.0", "Low": "3.0"}
    sarif_security_severity = security_severity_mapping.get(severity)
    if sarif_security_severity is None:
        print("[e] Could not convert severity to SARIF security severity")
    return sarif_security_severity


def parse_location(location: str):
    # Format: file_path:line:start_column:end_column or file_path:line:start_column-end_column
    parts = location.rsplit(":", 3)
    if len(parts) == 4:
        file_path, line_info, start_column_info, end_column_info = parts
    elif len(parts) == 3:
        file_path, line_info, column_range = parts
        if "-" in column_range:
            start_column_info, end_column_info = column_range.split("-", 1)
        else:
            start_column_info = column_range
            end_column_info = column_range
    else:
        raise ValueError(f"Invalid location format: {location}")
    start_line = int(line_info)
    start_column = int(start_column_info)
    end_column = int(end_column_info)
    return file_path, start_line, start_column, end_column


def save_json_output(container_output_file_path: Path, findings: list):
    with open(container_output_file_path, "w") as f:
        json.dump(findings, f, indent=4)


def write_sarif_output(output_file_path: Path, findings: list, arg_path: Optional[Path]):
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

                relative_file_path = (
                    str(Path(file_path).relative_to(arg_path))
                    if arg_path is not None
                    else str(Path(file_path))
                )

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
    markdown = "# radar Static Analysis Report\n\n"
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
