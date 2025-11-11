import json
from pathlib import Path
import pytest
import yaml
from utils.dsl.dsl import inject_code_lines, process_template_outputs, wrapped_exec


def normalize_template_name(name):
    """Convert template name to mock folder name format."""
    return name.lower().replace(" ", "_").replace("-", "_")


def extract_line_info(location):
    """
    Extract line:col info from location string.
    Example: '/path/to/file.rs:15:12-20' -> '15:12-20'
    """
    parts = location.rsplit(":", 2)
    if len(parts) >= 2:
        # Return line:col-col format
        return ":".join(parts[-2:])
    return location


# Expected detections for each template
# Format: "template_name": {"bad": ["tests/mocks/.../src/lib.rs:line:col-col", ...], "good": []}
EXPECTED_DETECTIONS = {
    "Account Data Matching": {
        "bad": [
            "tests/mocks/account_data_matching/bad/src/lib.rs:13:46-52"
        ], 
        "good": []
    },
    "PDA Sharing": {
        "bad": ["tests/mocks/pda_sharing/bad/src/lib.rs:2:17-22"],
        "good": []
    },
    "Random Authority Generation": {
        "bad": ["tests/mocks/cpi_authority_bypass/bad/src/lib.rs:10:33-43"],
        "good": []
    },
    "Account Precreation DoS": {
        "bad": ["tests/mocks/account_precreation_dos/bad/src/lib.rs:9:12-27"],
        "good": []
    }
}


def get_template_test_data():
    templates_path = Path("builtin_templates").absolute()
    mocks_path = Path("tests/mocks").absolute()
    
    template_test_data = []
    
    for yaml_file in templates_path.rglob("*.yaml"):
        with open(yaml_file, "r") as file:
            yaml_data = yaml.safe_load(file)
        
        template_name = yaml_data["name"]
        mock_folder_name = normalize_template_name(template_name)
        mock_folder = mocks_path / mock_folder_name
        
        if mock_folder.exists():
            bad_ast = mock_folder / "bad" / "ast.json"
            good_ast = mock_folder / "good" / "ast.json"
            
            if bad_ast.exists() and good_ast.exists():
                # Get expected detections if defined
                expected = EXPECTED_DETECTIONS.get(template_name, {"bad": None, "good": []})
                
                template_test_data.append({
                    "template_name": template_name,
                    "template_file": yaml_file,
                    "yaml_data": yaml_data,
                    "bad_ast": bad_ast,
                    "good_ast": good_ast,
                    "mock_folder": mock_folder_name,
                    "expected_bad_lines": expected["bad"],
                    "expected_good_lines": expected["good"],
                })
    
    return template_test_data


def run_template_on_ast(yaml_data, ast_file):
    code = yaml_data["rule"]
    
    with open(ast_file, "r") as file:
        ast_data = json.load(file)
    
    modified_code = inject_code_lines(code, [f"ast = parse_ast({ast_data}).items()"])
    template_outputs = wrapped_exec(modified_code)
    result = process_template_outputs(template_outputs, yaml_data)
    
    return result


@pytest.mark.parametrize("template_data", get_template_test_data(), ids=lambda x: x["template_name"])
def test_template_detects_bad_contract(template_data):
    if template_data["expected_bad_lines"] is None:
        pytest.skip(f"No expected detections defined for {template_data['template_name']}")
    
    result = run_template_on_ast(template_data["yaml_data"], template_data["bad_ast"])
    
    assert result.get("locations") is not None and len(result["locations"]) > 0, \
        f"Template '{template_data['template_name']}' FAILED to detect vulnerability in bad/{template_data['mock_folder']} contract"


@pytest.mark.parametrize("template_data", get_template_test_data(), ids=lambda x: x["template_name"])
def test_template_no_false_positives(template_data):
    if template_data["expected_bad_lines"] is None:
        pytest.skip(f"No expected detections defined for {template_data['template_name']}")
    
    result = run_template_on_ast(template_data["yaml_data"], template_data["good_ast"])
    
    locations = result.get("locations", [])
    assert len(locations) == 0, \
        f"Template '{template_data['template_name']}' has FALSE POSITIVE in good/{template_data['mock_folder']} contract.\n" \
        f"Detected at: {locations}"


@pytest.mark.parametrize("template_data", get_template_test_data(), ids=lambda x: x["template_name"])
def test_template_line_accuracy(template_data):
    if template_data["expected_bad_lines"] is None:
        pytest.skip(f"No expected detections defined for {template_data['template_name']}")
    
    result = run_template_on_ast(template_data["yaml_data"], template_data["bad_ast"])
    
    detected_locations = result.get("locations", [])
    assert len(detected_locations) > 0, \
        f"Template '{template_data['template_name']}' detected nothing in bad contract"
    
    detected_lines = [extract_line_info(loc) for loc in detected_locations]
    
    # For line accuracy validation, we check that:
    # 1. At least one detection occurred (already verified above)
    # 2. All detections have valid line info format (line:col-col)
    for line_info in detected_lines:
        assert ":" in line_info or "-" in line_info, \
            f"Invalid line info format in '{template_data['template_name']}': {line_info}"


@pytest.mark.parametrize("template_data", get_template_test_data(), ids=lambda x: x["template_name"])
def test_template_exact_line_detections(template_data):
    expected_bad_locations = template_data["expected_bad_lines"]
    expected_good_locations = template_data["expected_good_lines"]
    
    if expected_bad_locations is None:
        pytest.skip(f"No expected detections defined for {template_data['template_name']}")
    
    # Test bad contract detections
    result = run_template_on_ast(template_data["yaml_data"], template_data["bad_ast"])
    detected_locations = result.get("locations", [])
    
    # Convert detected locations from docker paths to relative paths with line:col info
    # Docker path: /radar_data/contract/src/lib.rs:9:38-53
    # Relative path: tests/mocks/template_name/bad/src/lib.rs:9:38-53
    detected_with_relative_paths = []
    for loc in detected_locations:
        # Extract line:col-col from the location
        line_info = extract_line_info(loc)
        # Reconstruct with relative path from api/ directory
        relative_path = f"tests/mocks/{template_data['mock_folder']}/bad/src/lib.rs:{line_info}"
        detected_with_relative_paths.append(relative_path)
    
    detected_set = set(detected_with_relative_paths)
    expected_set = set(expected_bad_locations)
    
    missing_detections = expected_set - detected_set
    extra_detections = detected_set - expected_set
    
    assert not missing_detections, \
        f"Template '{template_data['template_name']}' missed expected detections:\n{chr(10).join(missing_detections)}"
    assert not extra_detections, \
        f"Template '{template_data['template_name']}' found unexpected detections:\n{chr(10).join(extra_detections)}"
    
    # Verify expected_good_locations is empty (already enforced by test_template_no_false_positives)
    assert expected_good_locations == [], \
        f"Expected good locations should be empty list, got {expected_good_locations}"
