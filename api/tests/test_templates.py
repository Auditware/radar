import json
from pathlib import Path
import pytest
import yaml
from utils.dsl.dsl import inject_code_lines, process_template_outputs, wrapped_exec

expected_data = [
    (
        "Missing Signer Check",
        [
            "/radar_data/contract/programs/0-signer-authorization/insecure/src/lib.rs:14:3-9",
            "/radar_data/contract/programs/0-signer-authorization/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/1-account-data-matching/insecure/src/lib.rs:18:3-9",
            "/radar_data/contract/programs/1-account-data-matching/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/1-account-data-matching/secure/src/lib.rs:21:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/insecure/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/secure/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/2-owner-checks/insecure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/2-owner-checks/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/2-owner-checks/secure/src/lib.rs:25:3-9",
            "/radar_data/contract/programs/3-type-cosplay/insecure/src/lib.rs:23:3-9",
            "/radar_data/contract/programs/3-type-cosplay/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/3-type-cosplay/secure/src/lib.rs:26:3-9",
            "/radar_data/contract/programs/4-initialization/insecure/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/4-initialization/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/4-initialization/secure/src/lib.rs:28:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/insecure/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/secure/src/lib.rs:32:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/insecure/src/lib.rs:19:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/recommended/src/lib.rs:19:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/secure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/insecure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/secure/src/lib.rs:30:3-9",
            "/radar_data/contract/programs/8-pda-sharing/insecure/src/lib.rs:17:3-9",
            "/radar_data/contract/programs/8-pda-sharing/recommended/src/lib.rs:20:3-9",
            "/radar_data/contract/programs/8-pda-sharing/secure/src/lib.rs:20:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure-still-still/src/lib.rs:36:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure-still/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure/src/lib.rs:21:3-9",
            "/radar_data/contract/programs/9-closing-accounts/recommended/src/lib.rs:14:3-9",
            "/radar_data/contract/programs/9-closing-accounts/secure/src/lib.rs:56:3-9",
        ],
    ),
    (
        "Duplicate Mutable Accounts",
        [
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/insecure/src/lib.rs:10:13-19",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/insecure/src/lib.rs:11:13-19"
        ],
    ),
    (
        "Account Reinitialization",
        ["/radar_data/contract/programs/4-initialization/insecure/src/lib.rs:11:12-22"],
    ),
    (
        "Closing Accounts Insecurely",
        [
            "/radar_data/contract/programs/9-closing-accounts/insecure/src/lib.rs:12:45-55",
            "/radar_data/contract/programs/9-closing-accounts/insecure-still/src/lib.rs:15:45-55",
        ],
    ),
    (
        "Unvalidated Sysvar Account",
        [
            "/radar_data/contract/programs/10-sysvar-address-checking/insecure/src/lib.rs:10:45-49"
        ],
    ),
    (
        "Missing Owner Check",
        [
            "/radar_data/contract/programs/8-pda-sharing/secure/src/lib.rs:20:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/secure/src/lib.rs:32:3-9",
            "/radar_data/contract/programs/8-pda-sharing/insecure/src/lib.rs:17:3-9",
            "/radar_data/contract/programs/2-owner-checks/insecure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/4-initialization/secure/src/lib.rs:28:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/insecure/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/4-initialization/insecure/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/8-pda-sharing/recommended/src/lib.rs:20:3-9",
            "/radar_data/contract/programs/9-closing-accounts/secure/src/lib.rs:56:3-9",
            "/radar_data/contract/programs/3-type-cosplay/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/5-arbitrary-cpi/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure/src/lib.rs:21:3-9",
            "/radar_data/contract/programs/4-initialization/recommended/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/0-signer-authorization/secure/src/lib.rs:18:3-9",
            "/radar_data/contract/programs/1-account-data-matching/secure/src/lib.rs:21:3-9",
            "/radar_data/contract/programs/9-closing-accounts/recommended/src/lib.rs:14:3-9",
            "/radar_data/contract/programs/0-signer-authorization/insecure/src/lib.rs:14:3-9",
            "/radar_data/contract/programs/1-account-data-matching/insecure/src/lib.rs:18:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/secure/src/lib.rs:16:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure-still/src/lib.rs:29:3-9",
            "/radar_data/contract/programs/0-signer-authorization/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/insecure/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/secure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/secure/src/lib.rs:30:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/insecure/src/lib.rs:19:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/insecure/src/lib.rs:22:3-9",
            "/radar_data/contract/programs/10-sysvar-address-checking/recommended/src/lib.rs:15:3-9",
            "/radar_data/contract/programs/9-closing-accounts/insecure-still-still/src/lib.rs:36:3-9",
            "/radar_data/contract/programs/6-duplicate-mutable-accounts/recommended/src/lib.rs:19:3-9",
            "/radar_data/contract/programs/7-bump-seed-canonicalization/recommended/src/lib.rs:15:3-9",
        ],
    ),
    (
        "Arbitrary Cross-Program Invocation",
        ["/radar_data/contract/programs/5-arbitrary-cpi/insecure/src/lib.rs:10:12-15"],
    ),
]


@pytest.mark.parametrize("rule_name,expected_locations", expected_data)
def test_templates_consistency(rule_name, expected_locations):
    templates_path = Path("builtin_templates").absolute()
    yaml_files = list(templates_path.rglob("*.yaml"))

    results = []
    for yaml_file in yaml_files:
        with open(yaml_file, "r") as file:
            yaml_data = yaml.safe_load(file)

        code = yaml_data["rule"]

        with open("tests/mocks/ast_mock.json", "r") as file:
            generated_ast = json.load(file)

        modified_code = inject_code_lines(code, [f"ast = parse_ast({generated_ast}).items()"])

        template_outputs = wrapped_exec(modified_code)
        res = process_template_outputs(template_outputs, yaml_data)
        if res.get("locations") is not None:
            results.append(res)

    for result in results:
        if result["name"] == rule_name:
            assert sorted(result["locations"]) == sorted(
                expected_locations
            ), f"Mismatch in template results for {rule_name}"
