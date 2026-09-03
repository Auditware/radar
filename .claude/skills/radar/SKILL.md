---
name: radar
description: Use radar for smart contract security analysis, AST generation, and detection template development. Covers Rust (Anchor, native Solana, Stylus) and Solidity (standalone, Foundry). Triggers include scanning contracts for vulnerabilities, generating or inspecting a contract AST, writing or debugging a radar template, adding DSL utility functions, and contributing detection rules back to radar. Use when users mention radar, radar templates, the radar DSL, AST generation for Rust/Solidity/Anchor/Stylus/Foundry, or smart contract vulnerability scanning.
---

# radar

Radar scans smart contracts by running YAML **templates** - Python rules in a sandboxed DSL - over an enriched AST. Writing a good template is an auditing task, not a scripting task: the bar is a rule that catches a real vulnerability class it has never seen, never fires on correct code, and points at the exact line that is wrong.

This skill covers what you cannot infer from the repo. For CLI flags run `./radar --help` (authoritative, needs no Docker). For the full DSL method list read `docs/Rule-Functions.md`; for the wiki guide, `docs/How-to-Write-Templates.md`.

## How the pipeline actually works

| Source | Parser | Node class in rules |
|---|---|---|
| Rust - Anchor, native Solana, Stylus | `rust_syn` (syn 2 via syn-serde) | `RustASTNode` |
| Solidity, Foundry | `solc-select` + `solc` | `SolidityASTNode` |

The two node classes have **different method sets**. A rule gets one or the other based on its `language:` field - never both. Solidity is currently 68 of the 124 builtin templates, so check which side you are on before reaching for a method.

`radar` needs a running Docker daemon; every scan starts a compose stack. Template iteration does not - see the loop below.

## Three ways a template fails silently

Nearly every "my rule doesn't work" is one of these. None of them produce an error you will see.

1. **Every rule body runs inside `try: … except: continue`.** A misspelled method, wrong arity, or a Rust method called on a Solidity node raises, gets swallowed, and the file is skipped. No findings looks identical to no vulnerability. When a rule reports nothing, suspect a broken call before you suspect the pattern.
2. **The DSL is a sandbox with eight builtins:** `print len range dict list tuple set type`. No imports. `any()`, `all()`, `sorted()`, `enumerate()`, `str()`, `int()` raise `RuntimeError` - into the `except` above. Use `.nodes` truthiness, explicit loops, and `len()`.
3. **`language:` and `accent:` gate execution.** A template only runs when its `language` matches the detected project language (default `rust`) and, for Rust, its `accent` matches the detected framework. Get these wrong and the template is filtered out before it runs: no error, no failing test, no output. Solidity templates use `accent: ""` **and** `language: solidity`. There is no `accent: solidity`.

## The loop

**0. Do not write a duplicate.** 124 templates already ship. `./radar list-templates`, and grep `api/builtin_templates/*.yaml` for the vulnerability class. If one is close, extend it or sharpen its focus - a near-duplicate is a maintenance cost with no new coverage.

**1. Read the AST of a contract that has the bug.** `./radar --dev -p <path> --ast -o out.json` writes findings to `out.json` and the AST to **`ast.json` beside it** - two files. See `references/ast-shape.md`; the shape is not what you would guess.

**2. Draft the rule against what the AST actually contains,** not against the source you read. Inside a rule, `some_nodes.to_raw_ast_debug()` prints the enriched view (with `access_path`) at that point - add the call, do not wrap it in `print()`.

**3. Iterate in-process, not through Docker.** For Anchor templates:

```bash
cd api && poetry run python tests/check_scoping.py <template_stem>
```

Seconds per iteration, no daemon, and it reports detections on `bad/` and `good/` separately. It parses Rust live, so it needs `rust_syn` built once (`references/contributing.md`); inside the api container it is already there. It drives the Rust path only - Solidity rules iterate through the pytest suite.

**4. Prove both directions before you believe it.** The bad mock must detect; the good mock must be silent. One direction alone is not evidence.

**5. Pin what you just proved,** so the next person's tuning cannot quietly undo it - a noise fixture, a detection fixture, or both (see the gates below).

**6. Register it** in `EXPECTED_DETECTIONS` with exact `file:line:startcol-endcol` spans, and add the mock pair. A template with no entry is silently dropped from the accuracy suite and CI stays green. Full contract: `references/contributing.md`.

**7. Generate the fixtures, then run the full suite** - `cd api && poetry run python scripts/generate_fixtures.py`, then `make test-all` from the repo root. Plain `make test` skips the `active_runtime` suites, which are the ones that parse real source.

## The gates, and what each one exists to catch

Radar's test suite is a record of how detection rules have actually gone wrong here. Know which gate catches which mistake:

| Gate | Catches |
|---|---|
| `tests/check_scoping.py` | Rule fires on `bad/` but not `good/` - the fast dev loop |
| `tests/test_templates.py` | Wrong span; template missing its mock pair or its `EXPECTED_DETECTIONS` entry |
| `tests/noise_fixtures/` | False positives. Written after a benchmark found 24 of 52 findings landing on already-fixed code (#32) |
| `tests/detection_fixtures/` | Lost recall. Written after narrowing rules for precision silently killed four real detections (#33/#34) |
| `tests/corpus2_regression.py` | Out-of-sample drift, scored by someone else's mapping over real bugs |
| `tests/test_span_accuracy.py` | Findings whose line does not point at the cause |

## Zero false positives, honestly

Zero false positives is an absolute requirement, and it has an equal and opposite failure: a rule narrowed until it detects nothing is not precise, it is empty. That is exactly how four rules regressed in #33. Every tightening pass needs a detection fixture holding the other end.

- **Say how sure you are.** `certainty` is the auditor's judgment, not a form field. The corpus is honest about this: 121 of 124 templates declare `Low` or `Medium`; only 3 claim `High`. A heuristic with a plausible benign shape is `Low`, and that is a normal, shippable answer.
- **Point at the cause.** The reported span must land on the line that is wrong - not the enclosing function, not the file, never an import.
- **Generalize the pattern, don't fit the mock.** No hard-coded names, no contract-specific values. The rule should catch a variant it has never seen.
- **Never ship a rule that cannot fire.** Worse than no rule, because it reads as coverage the scanner does not have. If it is architecturally undetectable, record it in `ARCHITECTURALLY_UNDETECTABLE` with the reason instead of leaving it silently green.

## When to extend the DSL instead of the rule

A rule fighting the DSL is a signal, not a challenge. Median rule body is 23 lines; well past that usually means a missing utility. Escalate in this order:

1. A rule-level workaround - only if it is idiomatic and clean.
2. A new utility on `RustASTNode` / `SolidityASTNode` in `api/utils/dsl/`, following the traversal style of its neighbours. First check whether an existing util is merely faulty and needs a small fix - that is the better patch.
3. The core enrichment in `api/utils/ast.py` - rare, and only with a span test.

A good utility aggregates a relation that several rules will want (a lookup, a traversal, a comparison shape), not one contract's quirk. `references/util-authoring.md` carries the full protocol.

## Scanning

```bash
./radar -p <path>                      # scan
./radar -p <path> -o out.json          # .json | .md | .sarif by extension
./radar -p <path> --ast -o out.json    # + ast.json beside it
./radar -p <path> -t ./my-templates    # custom templates (dir or single .yaml)
./radar -p <path> --fail-on high       # CI gate: critical|high|medium|low|none
./radar -p <path> -b baseline.json     # suppress known findings
```

Exit codes: `0` clean, `1` findings at or above `--fail-on`, `2` operational error. Severities are `Critical|High|Medium|Low`; `--ignore` takes severities plus `uncertain`. `--ast` never skips scanning - it only adds output.

## References

- `references/ast-shape.md` - what `ast.json` really contains, and how to read it
- `references/dsl.md` - corrections to `docs/Rule-Functions.md`, and the Solidity method set
- `references/contributing.md` - the template schema and the full test contract
- `references/util-authoring.md` - the protocol for adding a DSL utility
