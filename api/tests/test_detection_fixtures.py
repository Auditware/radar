"""Detection-regression gate: rules must keep catching real bugs.

The bad/good mocks prove a rule works on its canonical example, and the scoping
gate proves it discriminates within a file. Neither catches the failure mode
where a rule is *narrowed* — to cut noise, or to score better on a corpus — until
it no longer detects a real vulnerability of its own class that happens to look
different from its mock.

That is exactly how four rules regressed in #33 (repaired in #34). Each file in
`detection_fixtures/` is a genuine vulnerability, named
`<template_stem>__<shape>.rs`, that the named template MUST report. Adding a
fixture here is the cheapest way to pin a detection you do not want traded away
for a cleaner benchmark number.

Runs the real Rust parser, so it is marked `active_runtime` like the scoping gate.
"""

from pathlib import Path

import pytest
import yaml

from tests.check_scoping import TEMPLATES
from tests.test_templates import run_template_on_rust_source

FIXTURES = Path(__file__).resolve().parent / "detection_fixtures"


def _cases():
    cases = []
    for fixture in sorted(FIXTURES.glob("*.rs")):
        stem = fixture.name.split("__")[0]
        cases.append((stem, fixture))
    return cases


CASES = _cases()


@pytest.mark.active_runtime
@pytest.mark.parametrize(
    "stem,fixture", CASES, ids=[f.stem for _, f in CASES]
)
def test_rule_still_detects(stem, fixture):
    template_path = TEMPLATES / f"{stem}.yaml"
    assert template_path.exists(), f"No template {stem}.yaml for fixture {fixture.name}"

    data = yaml.safe_load(template_path.read_text())
    result = run_template_on_rust_source(data, fixture)
    locations = result.get("locations", [])

    assert locations, (
        f"{stem} no longer detects {fixture.name}. This is a real vulnerability "
        f"the rule caught before; narrowing a rule until it misses this is a "
        f"regression, not a noise reduction."
    )


def test_detection_gate_covers_fixtures():
    """Guard against the gate silently covering nothing."""
    assert CASES, "No detection fixtures discovered"
