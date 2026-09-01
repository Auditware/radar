import json
from pathlib import Path
import pytest
import yaml
from utils.ast import generate_ast_for_rust_file
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
        "bad": ["tests/mocks/account_reinitialization/bad/src/lib.rs:11:12-22"],
        "good": []
    },
    "Arbitrary Cross-Program Invocation": {
        "bad": ["tests/mocks/arbitrary_cross_program_invocation/bad/src/lib.rs:10:12-24"],
        "good": []
    },
    "Arbitrary External Call": {
        "bad": [
            "tests/mocks/arbitrary_external_call/bad/arbitrary_external_call.sol:5:27-37"
        ],
        "good": []
    },
    "Callback Token Reentrancy": {
        "bad": [
            "tests/mocks/callback_token_reentrancy/bad/callback_token_reentrancy.sol:14:5-193"
        ],
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
    "Read-Only Reentrancy": {
        "bad": ["tests/mocks/read_only_reentrancy/bad/read_only_reentrancy.sol:22:25-51"],
        "good": []
    },
     "PDA Sharing": {
        "bad": ["tests/mocks/pda_sharing/bad/src/lib.rs:23:16-24"],
        "good": []
    },
    "Division Before Multiplication": {
        "bad": ["tests/mocks/division_before_multiplication/bad/src/lib.rs:10:20-26"],
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
    "Incorrect Reward Calculation": {
        "bad": [
            "tests/mocks/incorrect_reward_calculation/bad/incorrect_reward_calculation.sol:20:9-29"
        ],
        "good": []
    },
    "Insecure Clock Randomness": {
        "bad": [
            "tests/mocks/insecure_clock_randomness/bad/src/lib.rs:11:35-49"
        ],
        "good": []
    },
    "Insecure Randomness": {
        "bad": [
            "tests/mocks/insecure_randomness/bad/insecure_randomness.sol:8:51-65"
        ],
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
    "Missing Freeze Authority Check": {
        "bad": ["tests/mocks/missing_freeze_authority_check/bad/src/lib.rs:28:9-13"],
        "good": []
    },
    "Missing has_one Constraint": {
        "bad": ["tests/mocks/missing_has_one_constraint/bad/src/lib.rs:15:3-9"],
        "good": []
    },
    "Missing Owner Check": {
        "bad": ["tests/mocks/missing_owner_check/bad/src/lib.rs:21:3-9"],
        "good": []
    },
    "Missing Rent Exemption Check": {
        "bad": ["tests/mocks/missing_rent_exemption_check/bad/src/lib.rs:11:38-52"],
        "good": []
    },
    "Missing Token Authority Constraint": {
        "bad": ["tests/mocks/missing_token_authority_constraint/bad/src/lib.rs:29:21-28"],
        "good": []
    },
    "Missing Token Mint Constraint": {
        "bad": ["tests/mocks/missing_token_mint_constraint/bad/src/lib.rs:25:21-28"],
        "good": []
    },
    "Missing Signer Check": {
        "bad": ["tests/mocks/missing_signer_check/bad/src/lib.rs:15:3-9"],
        "good": []
    },
    "Type Cosplay": {
        "bad": ["tests/mocks/type_cosplay/bad/src/lib.rs:14:26-40"],
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
    "Vault Share Inflation": {
        "bad": [
            "tests/mocks/vault_share_inflation/bad/vault_share_inflation.sol:18:18-51"
        ],
        "good": []
    },
    "Wrong Function Visibility": {
        "bad": [
            "tests/mocks/wrong_function_visibility/bad/wrong_function_visibility.sol:6:5-70"
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
    "Snapshotless Governance Voting": {
        "bad": ["tests/mocks/snapshotless_governance_voting/bad/snapshotless_governance_voting.sol:18:26-40"],
        "good": []
    },
    "Spot Price Used As Oracle": {
        "bad": ["tests/mocks/spot_price_used_as_oracle/bad/spot_price_used_as_oracle.sol:15:50-65"],
        "good": []
    },
    "Storage Slot Collision": {
        "bad": ["tests/mocks/storage_slot_collision/bad/storage_slot_collision.sol:16:27-38"],
        "good": []
    },
    "Self Transfer Exploit": {
        "bad": ["tests/mocks/self_transfer_exploit/bad/self_transfer_exploit.sol:6:5-214"],
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
    "Public Skim Function": {
        "bad": ["tests/mocks/public_skim_function/bad/public_skim_function.sol:19:5-192"],
        "good": []
    },
    "Self-Referencing Token Swap": {
        "bad": ["tests/mocks/self_referencing_token_swap/bad/self_referencing_token_swap.sol:4:5-170"],
        "good": []
    },
    "Hardcoded External Dependency Address": {
        "bad": ["tests/mocks/hardcoded_external_dependency_address/bad/hardcoded_external_dependency_address.sol:4:5-72"],
        "good": []
    },
    "Hidden Fee Drain": {
        "bad": ["tests/mocks/hidden_fee_drain/bad/hidden_fee_drain.sol:21:9-29"],
        "good": []
    },
    "TWAP Window Too Small": {
        "bad": ["tests/mocks/twap_window_too_small/bad/twap_window_too_small.sol:16:25-27"],
        "good": []
    },
    "Unchecked Close Target": {
        "bad": ["tests/mocks/unchecked_close_target/bad/src/lib.rs:16:28-34"],
        "good": []
    },
    "Unchecked CPI Program Invoke": {
        "bad": ["tests/mocks/unchecked_cpi_program_invoke/bad/src/lib.rs:10:43-53"],
        "good": []
    },
    "Unchecked Low-Level Call Return": {
        "bad": ["tests/mocks/unchecked_low_level_call_return/bad/unchecked_low_level_call_return.sol:5:9-19"],
        "good": []
    },
    "Unchecked Token Account Owner": {
        "bad": ["tests/mocks/unchecked_token_account_owner/bad/src/lib.rs:29:15-22"],
        "good": []
    },
    "Anchor Spot Price Oracle": {
        "bad": ["tests/mocks/anchor_spot_price_oracle/bad/src/lib.rs:13:34-45"],
        "good": []
    },
    "Anchor Missing Min Output": {
        "bad": ["tests/mocks/anchor_missing_min_output/bad/src/lib.rs:9:53-60"],
        "good": []
    },
    "Anchor Reward Overflow": {
        "bad": ["tests/mocks/anchor_reward_overflow/bad/src/lib.rs:12:40-53"],
        "good": []
    },
    "Decimal To U64 Without Sign Check": {
        "bad": ["tests/mocks/decimal_to_u64_without_sign_check/bad/src/lib.rs:15:14-20"],
        "good": []
    },
    "Token Decimal Mismatch": {
        "bad": [
            "tests/mocks/token_decimal_mismatch/bad/token_decimal_mismatch.sol:5:16-72",
            "tests/mocks/token_decimal_mismatch/bad/token_decimal_mismatch.sol:9:16-65"
        ],
        "good": []
    },
    "Anchor Admin Without Timelock": {
        "bad": [
            "tests/mocks/anchor_admin_without_timelock/bad/src/lib.rs:10:28-46",
            "tests/mocks/anchor_admin_without_timelock/bad/src/lib.rs:15:28-36"
        ],
        "good": []
    },
    "Missing Transfer Amount Validation": {
        "bad": ["tests/mocks/missing_transfer_amount_validation/bad/src/lib.rs:24:16-24"],
        "good": []
    },
    "State Updated Before External Call": {
        "bad": ["tests/mocks/state_updated_before_external_call/bad/src/lib.rs:18:22-28"],
        "good": []
    },
    "Init If Needed Reinitialization": {
        "bad": ["tests/mocks/init_if_needed_reinitialization/bad/src/lib.rs:18:15-29"],
        "good": []
    },
    "Unconstrained UncheckedAccount": {
        "bad": ["tests/mocks/unconstrained_uncheckedaccount/bad/src/lib.rs:18:17-33"],
        "good": []
    },
    "Invoke Signed Unvalidated Seeds": {
        "bad": ["tests/mocks/invoke_signed_unvalidated_seeds/bad/src/lib.rs:12:18-31"],
        "good": []
    },
    "Stylus Missing Reentrancy Guard": {
        "bad": ["tests/mocks/stylus_missing_reentrancy_guard/bad/src/lib.rs:15:12-20"],
        "good": []
    },
    "Mint Decimals Scaling Ignored": {
        "bad": ["tests/mocks/mint_decimals_scaling_ignored/bad/src/lib.rs:11:31-43"],
        "good": []
    },
    "Chainlink L2 Sequencer Uptime Not Checked": {
        "bad": ["tests/mocks/chainlink_l2_sequencer_uptime_not_checked/bad/chainlink_l2_sequencer_uptime_not_checked.sol:11:34-58"],
        "good": []
    },
    "Ecrecover Missing Zero Address Check": {
        "bad": ["tests/mocks/ecrecover_missing_zero_address_check/bad/ecrecover_missing_zero_address_check.sol:5:26-34"],
        "good": []
    },
    "Unprotected Mint Entrypoint": {
        "bad": ["tests/mocks/unprotected_mint_entrypoint/bad/unprotected_mint_entrypoint.sol:7:5-126"],
        "good": []
    },
    "Missing Disable Initializers": {
        "bad": ["tests/mocks/missing_disable_initializers/bad/missing_disable_initializers.sol:3:1-300"],
        "good": []
    },
    "Unsafe Approve Race": {
        "bad": ["tests/mocks/unsafe_approve_race/bad/unsafe_approve_race.sol:9:9-21"],
        "good": []
    },
    "External Call In Loop": {
        "bad": ["tests/mocks/external_call_in_loop/bad/external_call_in_loop.sol:8:13-43"],
        "good": []
    },
    "Chainlink Answered In Round Not Checked": {
        "bad": ["tests/mocks/chainlink_answered_in_round_not_checked/bad/chainlink_answered_in_round_not_checked.sol:11:65-84"],
        "good": []
    },
    "Deprecated Chainlink Latest Answer": {
        "bad": ["tests/mocks/deprecated_chainlink_latest_answer/bad/deprecated_chainlink_latest_answer.sol:11:16-32"],
        "good": []
    },
    "Unsafe Usage of _mint": {
        "bad": ["tests/mocks/unsafe_usage_of__mint/bad/unsafe_usage_of__mint.sol:15:9-13"],
        "good": []
    },
    "Cross-Chain Message Missing Source Validation": {
        "bad": ["tests/mocks/cross_chain_message_missing_source_validation/bad/cross_chain_message_missing_source_validation.sol:17:5-197"],
        "good": []
    },
    "Unexplicit Imports": {
        "bad": ["tests/mocks/unexplicit_import/bad/unexplicit_import.sol:6:1-30"],
        "good": []
    },
    "Unexplicit Pragma": {
        "bad": ["tests/mocks/unexplicit_pragma/bad/unexplicit_pragma.sol:2:1-24"],
        "good": []
    },
    "Unsafe delegatecall": {
        "bad": ["tests/mocks/unsafe_delegatecall/bad/unsafe_delegatecall.sol:8:39-57"],
        "good": []
    },
    "Use of ABI Encode on Array of Arrays": {
        "bad": ["tests/mocks/use_of_abi_encode_on_array_of_arrays/bad/use_of_abi_encode_on_array_of_arrays.sol:8:26-35"],
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

        # Fall back to the template's filename when its display name does not
        # normalise to an existing folder. Without this a template whose `name`
        # drifted from its filename (e.g. cpi_authority_bypass -> "Random
        # Authority Generation") is silently never collected: no failure, no
        # skip, just absent from the suite - which is how several rules stayed
        # broken while the suite looked green.
        if not mock_folder.is_dir():
            stem_folder = mocks_path / yaml_file.stem
            if stem_folder.is_dir():
                mock_folder_name = yaml_file.stem
                mock_folder = stem_folder

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


def run_template_on_rust_source(yaml_data, source_file: Path):
    code = yaml_data["rule"]
    ast_data = generate_ast_for_rust_file(source_file)["ast"]
    modified_code = inject_code_lines(code, [f"ast = parse_ast({ast_data}, language='rust').items()"])
    template_outputs = wrapped_exec(modified_code)
    return process_template_outputs(template_outputs, yaml_data)


# Templates that cannot fire under the current architecture, with the reason.
# Kept explicit rather than left silently green: a rule that can never report is
# worse than no rule, because it reads as coverage the scanner does not have.
ARCHITECTURALLY_UNDETECTABLE = {
    "Missing Security Documentation": (
        "keys on Rust doc comments, which reach syn as a synthesized `doc` "
        "attribute. Source spans are resolved by searching the file text for the "
        "identifier, and the string 'doc' never appears in the source, so the "
        "node is dropped before the DSL sees it. Needs real parser spans "
        "(see the span discussion in PR #23) or removal."
    ),
}


@pytest.mark.parametrize("template_data", get_template_test_data(), ids=lambda x: x["template_name"])
def test_template_accuracy(template_data):
    """Comprehensive test: detects bad, no false positives, exact line matches."""
    reason = ARCHITECTURALLY_UNDETECTABLE.get(template_data["template_name"])
    if reason:
        pytest.xfail(f"{template_data['template_name']}: {reason}")

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

    # Exact-line metadata is optional, but its absence must not mean a template
    # goes unverified: the detect/no-false-positive contract above still holds.
    # Only the line-precision checks below need recorded expectations.
    if expected_bad_locations is None:
        pytest.skip(
            f"{template_data['template_name']}: detects bad and is clean on good; "
            "no expected-line metadata recorded for exact-location checks"
        )

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


RUNTIME_RUST_TEMPLATES = [
    {
        "name": "Anchor Spot Price Oracle",
        "yaml_file": Path("builtin_templates/anchor_spot_price_oracle.yaml"),
        "bad_source": Path("tests/mocks/anchor_spot_price_oracle/bad/src/lib.rs"),
        "good_source": Path("tests/mocks/anchor_spot_price_oracle/good/src/lib.rs"),
        "expected_bad_locations": ["tests/mocks/anchor_spot_price_oracle/bad/src/lib.rs:13:34-45"],
    },
    {
        "name": "Anchor Missing Min Output",
        "yaml_file": Path("builtin_templates/anchor_missing_min_output.yaml"),
        "bad_source": Path("tests/mocks/anchor_missing_min_output/bad/src/lib.rs"),
        "good_source": Path("tests/mocks/anchor_missing_min_output/good/src/lib.rs"),
        "expected_bad_locations": ["tests/mocks/anchor_missing_min_output/bad/src/lib.rs:9:53-60"],
    },
    {
        "name": "Decimal To U64 Without Sign Check",
        "yaml_file": Path("builtin_templates/decimal_to_u64_without_sign_check.yaml"),
        "bad_source": Path("tests/mocks/decimal_to_u64_without_sign_check/bad/src/lib.rs"),
        "good_source": Path("tests/mocks/decimal_to_u64_without_sign_check/good/src/lib.rs"),
        "expected_bad_locations": ["tests/mocks/decimal_to_u64_without_sign_check/bad/src/lib.rs:15:14-20"],
    },
    {
        "name": "Anchor Admin Without Timelock",
        "yaml_file": Path("builtin_templates/anchor_admin_without_timelock.yaml"),
        "bad_source": Path("tests/mocks/anchor_admin_without_timelock/bad/src/lib.rs"),
        "good_source": Path("tests/mocks/anchor_admin_without_timelock/good/src/lib.rs"),
        "expected_bad_locations": [
            "tests/mocks/anchor_admin_without_timelock/bad/src/lib.rs:10:28-46",
            "tests/mocks/anchor_admin_without_timelock/bad/src/lib.rs:15:28-36",
        ],
    },
]


@pytest.mark.active_runtime
@pytest.mark.parametrize("template_data", RUNTIME_RUST_TEMPLATES, ids=lambda x: x["name"])
def test_runtime_rust_template_accuracy(template_data):
    with open(template_data["yaml_file"], "r") as file:
        yaml_data = yaml.safe_load(file)

    bad_result = run_template_on_rust_source(yaml_data, template_data["bad_source"])
    good_result = run_template_on_rust_source(yaml_data, template_data["good_source"])

    bad_locations = set(bad_result.get("locations", []))
    good_locations = good_result.get("locations", [])

    assert bad_locations == set(template_data["expected_bad_locations"])
    assert good_locations == []
