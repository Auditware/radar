"""Live bad/good gate for Anchor templates.

`test_template_accuracy` only checks templates that have both recorded
expected-line metadata and a prebuilt `ast.json` fixture pair, which excludes
most Anchor rules. This drives each Anchor template against its `bad/` and
`good/` Rust mocks through the real parser so a rule that stops detecting its
bug, fires on the safe variant, or throws is caught in CI.

It parses Rust live (via `rust_syn`), so it is marked `active_runtime` and runs
under `make test-all` / the Docker image, not the fixture-only `make test`.
"""

import pytest

from tests.check_scoping import anchor_stems_with_rust_fixtures, scan_variants

STEMS = anchor_stems_with_rust_fixtures()

# Every Anchor template with Rust fixtures is now expected to detect its bad
# mock and stay clean on good. (Three rules that missed their own fixtures were
# repaired; keep this set empty so a future regression fails loudly rather than
# hiding behind an xfail.)
KNOWN_BROKEN = set()


@pytest.mark.active_runtime
@pytest.mark.parametrize("stem", STEMS, ids=STEMS)
def test_anchor_template_scoping(stem, request):
    if stem in KNOWN_BROKEN:
        request.node.add_marker(
            pytest.mark.xfail(reason="pre-existing: rule misses its own bad fixture", strict=False)
        )
    counts = scan_variants(stem)
    assert counts is not None, f"No Rust bad/good fixtures for {stem}"

    bad_errors = [h for h in counts["bad"] if str(h).startswith("ERROR")]
    good_errors = [h for h in counts["good"] if str(h).startswith("ERROR")]
    assert not bad_errors, f"{stem}: rule threw on bad fixture: {bad_errors}"
    assert not good_errors, f"{stem}: rule threw on good fixture: {good_errors}"

    bad_hits = [h for h in counts["bad"] if not str(h).startswith("ERROR")]
    assert bad_hits, f"{stem}: MISSED the bug - no detection on bad fixture"
    assert counts["good"] == [], f"{stem}: FALSE POSITIVE on good fixture: {counts['good']}"


def test_scoping_gate_covers_templates():
    """Guard against the gate silently covering nothing (empty parametrization)."""
    assert STEMS, "No Anchor templates with Rust bad/good fixtures were discovered"
