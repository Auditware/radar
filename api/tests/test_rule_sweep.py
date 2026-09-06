"""Gate: no rule may raise on any mock variant.

The bad/good gates run each rule against its own mock - the input its author had
in mind. A real scan points every selected rule at every file in the repo, so the
input that breaks a rule is almost always someone else's fixture. This runs that
cross product.

It is the gate that makes `RuleSkip` worth having: narrowing the bare handler
means a rule's own bug now propagates instead of being swallowed, and this is
what notices. Without it, a rule that throws on unfamiliar input still reports
nothing - it just reports nothing more loudly.

Marked `active_runtime`: it reads the generated `ast.json` fixtures, so it runs
under `make test-all` / the Docker image.
"""

import pytest

from tests.rule_sweep import sweep, templates, variants


@pytest.mark.active_runtime
def test_no_rule_raises_on_any_mock_variant():
    assert templates(), "no templates loaded"
    assert variants(), "no mock ast.json fixtures; run scripts/generate_fixtures.py"

    errors, _ = sweep()

    if errors:
        lines = [f"{len(errors)} rule failure(s) across the mock corpus:"]
        seen = set()
        for stem, variant, message, tb in errors:
            key = (stem, message)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"  {stem} on {variant}: {message}")
        pytest.fail("\n".join(lines))
