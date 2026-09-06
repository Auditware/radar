"""Score a candidate rule against a class's independent examples.

The examples in `class_examples/` are written from the definition of a
vulnerability class, not from any corpus case, and there are several shapes per
class. A rule has to satisfy all of them before it is worth pointing at the
held-out corpus - which is the point: a rule developed against one corpus case
and then scored on that case is in-sample, and no measurement can see it.

Shapes deliberately vary the spelling - Anchor and native, macro guards and
hand-written ones - because a rule matching one idiom passes its author's example
and misses everyone else's. Whoever adds a class should not then be the person
writing rules for it; that is a constraint on who does what, not something the
tooling can enforce.

    python tests/class_examples.py --list
    python tests/class_examples.py owner-check-after-cpi --rule path/to/draft.yaml

A pair passes only when the rule fires on the vulnerable file *and* stays silent
on its fix. Firing on both is not a detection, it is volume.
"""

import argparse
import sys
from pathlib import Path

import yaml

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))

EXAMPLES = TESTS / "class_examples"

# class -> the radar template that claims to detect it. Empty until a rule for
# the class exists; `test_class_examples.py` holds every listed rule to every
# pair, so adding an entry here is what puts a rule under this gate.
CLASS_RULES = {
    "instruction-introspection": "unvalidated_instruction_introspection",
    "owner-check-after-cpi": "owner_check_after_cpi",
    "program-account-validation": "unvalidated_cpi_program_account",
    "pda-derived-address-validation": "pda_address_not_verified",
    "mint-configuration-validation": "mint_configuration_unvalidated",
    "cpi-recursion": "cpi_self_recursion",
    "arithmetic-rounding-drain": "rounding_favours_caller",
}


def classes():
    return sorted(
        d.name for d in EXAMPLES.iterdir()
        if d.is_dir() and (d / "vulnerable").is_dir()
    )


def pairs(class_name: str):
    """(shape, vulnerable_path, fixed_path) for one class."""
    base = EXAMPLES / class_name
    found = []
    for vulnerable in sorted((base / "vulnerable").glob("*.rs")):
        fixed = base / "fixed" / vulnerable.name
        found.append((vulnerable.stem, vulnerable, fixed if fixed.exists() else None))
    return found


def score(candidate: dict, class_name: str):
    """Per-pair verdicts for one rule against one class."""
    from tests.test_templates import run_template_on_rust_source

    results = []
    for shape, vulnerable, fixed in pairs(class_name):
        row = {"shape": shape, "fires": None, "quiet": None, "error": None}
        try:
            row["fires"] = bool(
                run_template_on_rust_source(candidate, vulnerable).get("locations")
            )
            if fixed is not None:
                row["quiet"] = not run_template_on_rust_source(candidate, fixed).get("locations")
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        results.append(row)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("class_name", nargs="?")
    parser.add_argument("--rule", type=Path, help="candidate template to score")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list or not args.class_name:
        print(f"{'class':<34} {'pairs':>5}  shapes")
        for name in classes():
            shapes = [s for s, _, _ in pairs(name)]
            print(f"  {name:<32} {len(shapes):>5}  {', '.join(shapes)}")
        return 0

    if not args.rule:
        parser.error("--rule is required when a class is named")

    candidate = yaml.safe_load(args.rule.read_text())
    rows = score(candidate, args.class_name)

    print(f"\n{candidate.get('name', args.rule.stem)} vs {args.class_name}\n")
    passed = 0
    for row in rows:
        if row["error"]:
            verdict = f"ERROR {row['error']}"
        elif row["fires"] and row["quiet"]:
            verdict, passed = "pass", passed + 1
        elif not row["fires"]:
            verdict = "MISSES the bug"
        else:
            verdict = "fires on the fix too"
        print(f"  {row['shape']:<40} {verdict}")
    print(f"\n  {passed}/{len(rows)} pair(s) satisfied")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
