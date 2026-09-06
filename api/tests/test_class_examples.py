"""Gate: the class examples stay well-formed, and any rule claiming a class satisfies them.

Two jobs. The first is cheap and always runs: every vulnerable example must have
a fix of the same name, so a pair cannot silently become a one-sided file that
proves nothing. The second holds any rule listed in `CLASS_RULES` to every pair
in its class - firing on the bug and silent on the fix - which is what stops a
rule from being tuned to one shape.
"""

from pathlib import Path

import pytest
import yaml

from tests.class_examples import CLASS_RULES, classes, pairs, score

TEMPLATES = Path(__file__).resolve().parent.parent / "builtin_templates"


@pytest.mark.parametrize("class_name", classes())
def test_every_vulnerable_example_has_a_matching_fix(class_name):
    missing = [shape for shape, _, fixed in pairs(class_name) if fixed is None]
    assert not missing, (
        f"{class_name}: no fixed counterpart for {missing}. A vulnerable example "
        "with no fix cannot distinguish a rule that detects the bug from one that "
        "reports the whole file."
    )


@pytest.mark.parametrize("class_name", classes())
def test_class_has_more_than_one_shape(class_name):
    shapes = pairs(class_name)
    assert len(shapes) > 1, (
        f"{class_name}: only {len(shapes)} shape. One shape is one idiom, and a "
        "rule that matches one idiom is exactly what passes its author's example "
        "and misses everyone else's."
    )


@pytest.mark.active_runtime
@pytest.mark.parametrize("class_name,stem", sorted(CLASS_RULES.items()))
def test_rule_satisfies_every_shape_of_its_class(class_name, stem):
    template_path = TEMPLATES / f"{stem}.yaml"
    assert template_path.exists(), f"{class_name} maps to missing template {stem}.yaml"

    candidate = yaml.safe_load(template_path.read_text())
    rows = score(candidate, class_name)

    failures = []
    for row in rows:
        if row["error"]:
            failures.append(f"{row['shape']}: raised {row['error']}")
        elif not row["fires"]:
            failures.append(f"{row['shape']}: misses the bug")
        elif not row["quiet"]:
            failures.append(f"{row['shape']}: fires on the fix too")

    assert not failures, f"{stem} on {class_name}:\n  " + "\n  ".join(failures)


@pytest.mark.active_runtime
@pytest.mark.parametrize("class_name", classes())
def test_every_example_parses(class_name):
    """An example the parser cannot read proves nothing and fails silently.

    `run_template_on_rust_source` raises on a parse error, which the scoring
    helper records per pair - so a malformed example would show up as a rule
    that errors rather than as an example that is broken. Checking it here
    keeps the blame in the right place.
    """
    from utils.ast import generate_ast_for_rust_file

    broken = []
    for shape, vulnerable, fixed in pairs(class_name):
        for path in (vulnerable, fixed):
            if path is None:
                continue
            try:
                if not generate_ast_for_rust_file(path)["ast"]:
                    broken.append(f"{path.name}: parsed to zero items")
            except Exception as exc:
                broken.append(f"{path.name}: {type(exc).__name__}: {exc}")

    assert not broken, f"{class_name}:\n  " + "\n  ".join(broken)
