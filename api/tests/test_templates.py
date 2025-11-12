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
    "Account Precreation DoS": {
        "bad": ["tests/mocks/account_precreation_dos/bad/src/lib.rs:9:12-27"],
        "good": []
    },
    "Account Reinitialization": {
        "bad": ["tests/mocks/account_reinitialization/bad/src/lib.rs:9:12-22"],
        "good": []
    },
    "Arbitrary Cross-Program Invocation": {
        "bad": ["tests/mocks/arbitrary_cross_program_invocation/bad/src/lib.rs:10:12-24"],
        "good": []
    },
    "Closing Accounts Insecurely": {
        "bad": ["tests/mocks/closing_accounts_insecurely/bad/src/lib.rs:11:64-74"],
        "good": []
    },
    "Random Authority Generation": {
        "bad": ["tests/mocks/cpi_authority_bypass/bad/src/lib.rs:10:33-43"],
        "good": []
    },
     "PDA Sharing": {
        "bad": ["tests/mocks/pda_sharing/bad/src/lib.rs:18:16-24"],
        "good": []
    },
    "Division Before Multiplication": {
        "bad": ["tests/mocks/division_before_multiplication/bad/src/lib.rs:9:54-60"],
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
def test_template_accuracy(template_data):
    """Comprehensive test: detects bad, no false positives, exact line matches."""
    if template_data["expected_bad_lines"] is None:
        pytest.skip(f"No expected detections defined for {template_data['template_name']}")
    
    expected_bad_locations = template_data["expected_bad_lines"]
    expected_good_locations = template_data["expected_good_lines"]
    
    # Test 1: Bad contract - should detect vulnerabilities
    bad_result = run_template_on_ast(template_data["yaml_data"], template_data["bad_ast"])
    bad_locations = bad_result.get("locations", [])
    
    assert len(bad_locations) > 0, \
        f"FAILED to detect vulnerability in bad contract"
    
    # Test 2: Good contract - should have no false positives
    good_result = run_template_on_ast(template_data["yaml_data"], template_data["good_ast"])
    good_locations = good_result.get("locations", [])
    
    assert len(good_locations) == 0, \
        f"FALSE POSITIVE in good contract at: {good_locations}"
    
    # Test 3: Validate line info format
    for loc in bad_locations:
        line_info = extract_line_info(loc)
        assert ":" in line_info or "-" in line_info, \
            f"Invalid line info format: {line_info}"
    
    # Test 4: Exact line detections match expected
    detected_with_relative_paths = []
    for loc in bad_locations:
        line_info = extract_line_info(loc)
        relative_path = f"tests/mocks/{template_data['mock_folder']}/bad/src/lib.rs:{line_info}"
        detected_with_relative_paths.append(relative_path)
    
    detected_set = set(detected_with_relative_paths)
    expected_set = set(expected_bad_locations)
    
    missing_detections = expected_set - detected_set
    extra_detections = detected_set - expected_set
    
    assert not missing_detections, \
        f"Missed expected detections:\n{chr(10).join(missing_detections)}"
    assert not extra_detections, \
        f"Found unexpected detections:\n{chr(10).join(extra_detections)}"
    
    assert expected_good_locations == [], \
        f"Expected good locations should be empty list, got {expected_good_locations}"


def test_all_templates_have_required_fields_in_order():
    """Verify all templates have required fields in the correct order."""
    templates_path = Path("builtin_templates").absolute()
    
    # Expected field order (description before severity/certainty is more logical)
    EXPECTED_FIELD_ORDER = [
        "version",
        "author", 
        "accent",
        "name",
        "description",
        "severity",
        "certainty",
        "vulnerable_example",
        "rule"
    ]
    
    REQUIRED_FIELDS = {"version", "author", "accent", "name", "description", "severity", "certainty", "rule"}
    
    issues = []
    
    for yaml_file in sorted(templates_path.glob("*.yaml")):
        with open(yaml_file, "r") as f:
            content = f.read()
            template = yaml.safe_load(content)
        
        template_name = template.get("name", yaml_file.name)
        
        # Check required fields exist
        missing_fields = REQUIRED_FIELDS - set(template.keys())
        if missing_fields:
            issues.append(f"{yaml_file.name}: Missing required fields: {missing_fields}")
            continue
        
        # Extract field order from raw content
        actual_order = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    field = line.split(':')[0].strip()
                    if field in EXPECTED_FIELD_ORDER and field not in actual_order:
                        actual_order.append(field)
        
        # Check field order matches expected
        expected_present = [f for f in EXPECTED_FIELD_ORDER if f in template.keys()]
        actual_present = [f for f in actual_order if f in EXPECTED_FIELD_ORDER]
        
        if expected_present != actual_present:
            issues.append(
                f"{yaml_file.name}: Incorrect field order\n"
                f"  Expected: {expected_present}\n"
                f"  Actual:   {actual_present}"
            )
    
    assert not issues, \
        f"Template field validation failed:\n" + "\n".join(issues)
