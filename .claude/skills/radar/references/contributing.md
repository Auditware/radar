# Contributing a template

## Schema

Required: `version`, `author`, `accent`, `name`, `description`, `severity`, `certainty`, `rule`. `vulnerable_example` is optional. **Field order is enforced** by `test_all_templates_have_required_fields_in_order`:

```yaml
version: 0.1.0
author: your-handle
accent: anchor          # anchor | stylus | "" for Solidity - required even when empty
language: solidity      # omit for Rust (defaults to rust); required for Solidity
name: Account Data Matching
description: One sentence on the vulnerability and why it matters.
severity: Critical|High|Medium|Low
certainty: High|Medium|Low
vulnerable_example: https://github.com/Auditware/radar/blob/main/api/tests/mocks/<name>/bad/src/lib.rs#L13
rule: |
  for source, nodes in ast:
      ...
```

`accent` and `language` decide whether the template runs at all - see SKILL.md.

## Mocks

The folder name is the **display name**, normalized (lowercased, spaces and hyphens to underscores); the template filename stem also resolves. `test_every_template_has_a_mock_pair_on_disk` fails the build for a template with neither.

```
api/tests/mocks/<name>/bad/src/lib.rs      # Rust: vulnerable
api/tests/mocks/<name>/good/src/lib.rs     # Rust: the same code, fixed
api/tests/mocks/<name>/bad/<name>.sol      # Solidity: file sits at the top of bad/
api/tests/mocks/<name>/good/<name>.sol
```

Keep the pair minimal and differing only in the vulnerability, so the good mock is real evidence of precision rather than a different program.

## Register the expected detections

`api/tests/test_templates.py`, keyed by display name, with exact spans:

```python
"Account Data Matching": {
    "bad": ["tests/mocks/account_data_matching/bad/src/lib.rs:13:46-52"],
    "good": []
},
```

The suite asserts both directions and both ways: a missed detection **and** an unexpected one fail. `good` must be `[]`. Get spans by running the template and reading the reported locations - do not guess them.

A template with no entry here is skipped by the accuracy suite without a failure or a skip message. That is the repo's known silent-coverage failure; do not add to it.

## Pin the behaviour you proved

Both gates are keyed `<template_stem>__<shape>.rs` and run the real parser:

- `api/tests/noise_fixtures/` - a **safe** shape this rule must never fire on. Add one whenever you fix a false positive, ideally minimized from the code that produced it.
- `api/tests/detection_fixtures/` - a **genuine** vulnerability of this class, shaped differently from the mock, that the rule must keep reporting. Add one whenever you narrow a rule.

## Setup for the local loop

Anything that parses real source (`check_scoping.py`, the `active_runtime` suites, fixture generation) needs the Rust extension built and installed where the loader looks for it - the same steps CI runs:

```bash
cd api && poetry install --no-root
cd api/rust_syn_wrapper && cargo build --release
sudo mkdir -p /api/utils && sudo cp target/release/librust_syn.so /api/utils/rust_syn.so
```

Solidity additionally needs `solc-select`. Inside the api container both are already present, so this is only for working outside Docker.

## Run

```bash
cd api && poetry run python tests/check_scoping.py <stem>   # fast loop, Anchor/Rust
cd api && poetry run python scripts/generate_fixtures.py    # build ast.json fixtures
make test-all                                               # includes active_runtime
make test                                                   # excludes it - not sufficient alone
make test-controller                                        # CLI/output layer
cd api && poetry run python tests/corpus2_regression.py     # out-of-sample, not a merge gate
```

`generate_fixtures.py` needs the Rust and solc toolchains; both are present in the Docker image.

## Before opening a PR

- Detects the bad mock, silent on the good mock, spans on the causing line.
- Noise and/or detection fixture added for what you changed.
- `EXPECTED_DETECTIONS` entry present with exact spans.
- No duplicate of an existing template - extended one where the class overlapped.
- `certainty` honestly set; a `Low` heuristic labelled `High` is a defect.
- `make test-all` green.
