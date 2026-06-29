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
    Example: '/path/to/bad.sol:15:12-20' -> '15:12-20'
    """
    parts = location.rsplit(":", 2)
    if len(parts) >= 2:
        return ":".join(parts[-2:])
    return location


def get_mock_sol_filename(mock_folder: Path, kind: str) -> str:
    """Return the .sol filename (if any) inside mock_folder/kind/."""
    sol_files = list((mock_folder / kind).glob("*.sol"))
    if sol_files:
        return sol_files[0].name
    return "src/lib.rs"


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
    },
    "Exponential Calculation Complexity": {
        "bad": ["tests/mocks/exponential_calculation_complexity/bad/src/lib.rs:13:12-21"],
        "good": []
    },
    "Improper External Account Access": {
        "bad": ["tests/mocks/improper_external_account_access/bad/src/lib.rs:13:12-21"],
        "good": []
    },
    "Incorrect Token Calculation": {
        "bad": ["tests/mocks/incorrect_token_calculation/bad/src/lib.rs:14:12-16"],
        "good": []
    },
    "Integer Division Overflow": {
        "bad": ["tests/mocks/integer_division_overflow/bad/src/lib.rs:12:12-21"],
        "good": []
    },
    "Invalid Function Attributes": {
        "bad": ["tests/mocks/invalid_function_attributes/bad/src/lib.rs:12:7-14"],
        "good": []
    },
    "Missing Owner Check": {
        "bad": ["tests/mocks/missing_owner_check/bad/src/lib.rs:20:3-9"],
        "good": []
    },
    "Missing Signer Check": {
        "bad": ["tests/mocks/missing_signer_check/bad/src/lib.rs:15:3-9"],
        "good": []
    },
    "Type Cosplay": {
        "bad": ["tests/mocks/type_cosplay/bad/src/lib.rs:11:33-48"],
        "good": []
    },
    "Unchecked Arithmetics": {
        "bad": ["tests/mocks/unchecked_arithmetics/bad/src/lib.rs:16:22-25"],
        "good": []
    },
    "Immutable State Mutation": {
        "bad": ["tests/mocks/immutable_state_mutation/bad/src/lib.rs:15:29-32"],
        "good": []
    },
    "Missing Two Step Ownership Transfer": {
        "bad": [
            "tests/mocks/missing_two_step_ownership_transfer/bad/missing_two_step_ownership_transfer.sol:10:5-142"
        ],
        "good": []
    },
    "ERC20 Permit Deadline Not Checked": {
        "bad": [
            "tests/mocks/erc20_permit_deadline_not_checked/bad/erc20_permit_deadline_not_checked.sol:16:9-20"
        ],
        "good": []
    },
    "Missing ERC20 Return Value Check": {
        "bad": [
            "tests/mocks/missing_erc20_return_value_check/bad/missing_erc20_return_value_check.sol:15:9-22"
        ],
        "good": []
    },
    "Fee On Transfer Incompatibility": {
        "bad": [
            "tests/mocks/fee_on_transfer_incompatibility/bad/fee_on_transfer_incompatibility.sol:16:9-26"
        ],
        "good": []
    },
    "Signature Missing Nonce Or Chainid": {
        "bad": [
            "tests/mocks/signature_missing_nonce_or_chainid/bad/signature_missing_nonce_or_chainid.sol:6:16-24"
        ],
        "good": []
    },
    "UpgradeTo Without Access Control": {
        "bad": [
            "tests/mocks/upgradeto_without_access_control/bad/upgradeto_without_access_control.sol:6:5-88"
        ],
        "good": []
    },
    "Missing Storage Gap Upgradeable": {
        "bad": [
            "tests/mocks/missing_storage_gap_upgradeable/bad/missing_storage_gap_upgradeable.sol:3:1-81"
        ],
        "good": []
    },
    "Unbounded Loop Over Dynamic Array": {
        "bad": [
            "tests/mocks/unbounded_loop_over_dynamic_array/bad/unbounded_loop_over_dynamic_array.sol:7:9-86"
        ],
        "good": []
    },
    "Unsafe Integer Downcast": {
        "bad": [
            "tests/mocks/unsafe_integer_downcast/bad/unsafe_integer_downcast.sol:5:21-39"
        ],
        "good": []
    },
    "No Emergency Pause Mechanism": {
        "bad": [
            "tests/mocks/no_emergency_pause_mechanism/bad/no_emergency_pause_mechanism.sol:16:5-156",
            "tests/mocks/no_emergency_pause_mechanism/bad/no_emergency_pause_mechanism.sol:21:5-138"
        ],
        "good": []
    },
    "Stale Chainlink Price": {
        "bad": ["tests/mocks/stale_chainlink_price/bad/stale_chainlink_price.sol:15:51-72"],
        "good": []
    },
    "Missing Flash Loan Callback Validation": {
        "bad": ["tests/mocks/missing_flash_loan_callback_validation/bad/missing_flash_loan_callback_validation.sol:6:5-209"],
        "good": []
    },
    "Unvalidated Proxy Initializer": {
        "bad": ["tests/mocks/unvalidated_proxy_initializer/bad/unvalidated_proxy_initializer.sol:6:5-78"],
        "good": []
    },
    "Missing Deadline On Swap": {
        "bad": ["tests/mocks/missing_deadline_on_swap/bad/missing_deadline_on_swap.sol:29:27-41"],
        "good": []
    },
    "Governance Execute Without Timelock": {
        "bad": ["tests/mocks/governance_execute_without_timelock/bad/governance_execute_without_timelock.sol:12:5-258"],
        "good": []
    },
    "Missing Slippage On Swap": {
        "bad": ["tests/mocks/missing_slippage_on_swap/bad/missing_slippage_on_swap.sol:27:35-35"],
        "good": []
    },
    "Chainlink Min Max Circuit Breaker": {
        "bad": ["tests/mocks/chainlink_min_max_circuit_breaker/bad/chainlink_min_max_circuit_breaker.sol:15:34-55"],
        "good": []
    },
    "ERC4626 Share Inflation": {
        "bad": ["tests/mocks/erc4626_share_inflation/bad/erc4626_share_inflation.sol:15:5-213"],
        "good": []
    },
    "Spot Price Used As Oracle": {
        "bad": ["tests/mocks/spot_price_used_as_oracle/bad/spot_price_used_as_oracle.sol:15:50-65"],
        "good": []
    },
    "Selfdestruct In Implementation": {
        "bad": ["tests/mocks/selfdestruct_in_implementation/bad/selfdestruct_in_implementation.sol:18:9-20"],
        "good": []
    },
    "ETH Send or Transfer Usage": {
        "bad": ["tests/mocks/eth_send_or_transfer_usage/bad/eth_send_or_transfer_usage.sol:5:9-35"],
        "good": []
    },
    "Unprotected Configuration Setters": {
        "bad": ["tests/mocks/unprotected_configuration_setters/bad/unprotected_configuration_setters.sol:6:5-68"],
        "good": []
    },
    "Missing Array Length Equality Check": {
        "bad": ["tests/mocks/missing_array_length_equality_check/bad/missing_array_length_equality_check.sol:14:5-221"],
        "good": []
    },
    "Missing sqrtPriceLimitX96 on Pool Swap": {
        "bad": ["tests/mocks/missing_sqrtpricelimitx96_on_pool_swap/bad/missing_sqrtpricelimitx96_on_pool_swap.sol:15:59-59"],
        "good": []
    },
    "Permit Front-Run Griefing": {
        "bad": ["tests/mocks/permit_front_run_griefing/bad/permit_front_run_griefing.sol:16:9-20"],
        "good": []
    },
    "Self-Referencing Token Swap": {
        "bad": ["tests/mocks/self_referencing_token_swap/bad/self_referencing_token_swap.sol:4:5-170"],
        "good": []
    },
    "Reentrancy via ERC777 Hook": {
        "bad": ["tests/mocks/reentrancy_via_erc777_hook/bad/reentrancy_via_erc777_hook.sol:14:5-257"],
        "good": []
    },
    "Hardcoded External Dependency Address": {
        "bad": ["tests/mocks/hardcoded_external_dependency_address/bad/hardcoded_external_dependency_address.sol:4:5-72"],
        "good": []
    },
    "TWAP Window Too Small": {
        "bad": ["tests/mocks/twap_window_too_small/bad/twap_window_too_small.sol:16:25-27"],
        "good": []
    },
    "Unchecked Low-Level Call Return": {
        "bad": ["tests/mocks/unchecked_low_level_call_return/bad/unchecked_low_level_call_return.sol:5:9-19"],
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
                
                language = yaml_data.get("language", "rust")
                bad_sol_file = get_mock_sol_filename(mock_folder, "bad")
                template_test_data.append({
                    "template_name": template_name,
                    "template_file": yaml_file,
                    "yaml_data": yaml_data,
                    "bad_ast": bad_ast,
                    "good_ast": good_ast,
                    "mock_folder": mock_folder_name,
                    "language": language,
                    "bad_source_file": bad_sol_file,
                    "expected_bad_lines": expected["bad"],
                    "expected_good_lines": expected["good"],
                })
    
    return template_test_data


def run_template_on_ast(yaml_data, ast_file, language: str = "rust"):
    code = yaml_data["rule"]
    
    with open(ast_file, "r") as file:
        ast_data = json.load(file)
    
    modified_code = inject_code_lines(code, [f"ast = parse_ast({ast_data}, language={repr(language)}).items()"])
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
    bad_result = run_template_on_ast(template_data["yaml_data"], template_data["bad_ast"], template_data.get("language", "rust"))
    bad_locations = bad_result.get("locations", [])
    
    assert len(bad_locations) > 0, \
        f"FAILED to detect vulnerability in bad contract"
    
    # Test 2: Good contract - should have no false positives
    good_result = run_template_on_ast(template_data["yaml_data"], template_data["good_ast"], template_data.get("language", "rust"))
    good_locations = good_result.get("locations", [])
    
    assert len(good_locations) == 0, \
        f"FALSE POSITIVE in good contract at: {good_locations}"
    
    # Test 3: Validate line info format
    for loc in bad_locations:
        line_info = extract_line_info(loc)
        assert ":" in line_info or "-" in line_info, \
            f"Invalid line info format: {line_info}"
    
    # Test 4: Exact line detections match expected
    bad_source_file = template_data.get("bad_source_file", "src/lib.rs")
    detected_with_relative_paths = []
    for loc in bad_locations:
        line_info = extract_line_info(loc)
        relative_path = f"tests/mocks/{template_data['mock_folder']}/bad/{bad_source_file}:{line_info}"
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
