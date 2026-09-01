"""No-false-positive gate: rules must stay silent on already-correct code.

The detection-regression gate (`test_detection_fixtures.py`) pins the recall
side - a narrowed rule must still catch real bugs. This is its mirror for the
precision side: each file here is a *safe* pattern that a named rule used to fire
on, and must never fire on again.

The motivation is issue #32: an independent benchmark found 24 of radar's 52
findings on the sealevel-attacks corpus landed on the `secure`/`recommended`
(fixed) variants. Most of those were genuine false positives from the generic
Anchor rules. As each is repaired, the exact safe shape is captured here so a
future "make it fire a little more" change cannot quietly bring the noise back.

Files are named `<template_stem>__<shape>.rs`. Faithful minimisations of the
corpus files are preferred over invented ones, so the gate tracks what the
benchmark actually measured. Runs the real Rust parser, so it is marked
`active_runtime` like the other source-level gates.
"""

from pathlib import Path

import pytest
import yaml

from tests.check_scoping import TEMPLATES
from tests.test_templates import run_template_on_rust_source

FIXTURES = Path(__file__).resolve().parent / "noise_fixtures"


def _cases():
    cases = []
    for fixture in sorted(FIXTURES.glob("*.rs")):
        stem = fixture.name.split("__")[0]
        cases.append((stem, fixture))
    return cases


CASES = _cases()


@pytest.mark.active_runtime
@pytest.mark.parametrize("stem,fixture", CASES, ids=[f.stem for _, f in CASES])
def test_rule_stays_silent(stem, fixture):
    template_path = TEMPLATES / f"{stem}.yaml"
    assert template_path.exists(), f"No template {stem}.yaml for fixture {fixture.name}"

    data = yaml.safe_load(template_path.read_text())
    result = run_template_on_rust_source(data, fixture)
    locations = result.get("locations", [])

    assert not locations, (
        f"{stem} fired on {fixture.name}, which is a fixed/safe pattern it must "
        f"not report. Locations: {locations}. This is the false-positive class "
        f"from issue #32 regressing - a rule was widened until it flags "
        f"already-correct code again."
    )


def test_noise_gate_covers_fixtures():
    """Guard against the gate silently covering nothing."""
    assert CASES, "No noise fixtures discovered"
