"""Sweep every rule across every mock variant and report the ones that raise.

A rule that throws reports nothing, and until `RuleSkip` landed, nothing said so:
the bare `except:` every template guards its loop with also caught the rule's own
bugs, so a broken rule and a clean scan produced the same empty result.

The bad/good gates only run a rule against *its own* mock, which is the one input
its author had in mind. Real scans point every selected rule at every file in the
repo, so the inputs that break a rule are almost always someone else's fixture.
This runs that cross product - each rule against all 254 mock variants - which is
the cheapest approximation of a real scan's input diversity that we own.

Usage:
    python tests/rule_sweep.py            # sweep, print any rule that raises
    python tests/rule_sweep.py --verbose  # also print per-rule detection totals
"""

import argparse
import json
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TESTS = Path(__file__).resolve().parent
_REPO_TEMPLATES = TESTS.parent / "builtin_templates"
TEMPLATES = _REPO_TEMPLATES if _REPO_TEMPLATES.is_dir() else Path("/api/builtin_templates")
MOCKS = TESTS / "mocks"


def variants():
    """Every mock variant directory that has a generated `ast.json`, with its language.

    Language is read from the sources present rather than declared, the same way
    `detect_language_from_path` decides at scan time.
    """
    found = []
    for ast_path in sorted(MOCKS.glob("*/*/ast.json")):
        vdir = ast_path.parent
        language = "solidity" if list(vdir.rglob("*.sol")) else "rust"
        found.append((vdir, language, ast_path))
    return found


def templates():
    loaded = []
    for path in sorted(TEMPLATES.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text())
        except Exception:
            continue
        if isinstance(data, dict) and "rule" in data:
            loaded.append((path.stem, data))
    return loaded


def sweep(only=None):
    """Run every template over every same-language variant.

    Returns (errors, detections):
      errors     - list of (stem, variant, exception string, traceback)
      detections - {stem: total locations reported across all variants}
    """
    from tests.test_templates import run_template_on_ast

    errors = []
    detections = defaultdict(int)
    all_variants = variants()

    for stem, data in templates():
        if only and stem not in only:
            continue
        language = data.get("language", "rust")
        for vdir, vlanguage, ast_path in all_variants:
            if vlanguage != language:
                continue
            try:
                result = run_template_on_ast(data, ast_path, language)
            except Exception as exc:
                errors.append((stem, vdir.relative_to(MOCKS), f"{type(exc).__name__}: {exc}", traceback.format_exc()))
                continue
            detections[stem] += len(result.get("locations", []))
    return errors, detections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", type=Path, help="write per-rule detection totals here")
    parser.add_argument("stems", nargs="*")
    args = parser.parse_args()

    errors, detections = sweep(only=set(args.stems) or None)

    n_templates = len(args.stems) or len(templates())
    print(f"[i] swept {n_templates} template(s) over {len(variants())} mock variant(s)")

    if args.verbose:
        for stem in sorted(detections):
            print(f"    {detections[stem]:5d}  {stem}")

    if args.json:
        args.json.write_text(json.dumps(dict(sorted(detections.items())), indent=1))
        print(f"[i] detection totals written to {args.json}")

    if not errors:
        print("[i] 0 rules raise.")
        return 0

    by_stem = defaultdict(list)
    for stem, variant, message, _ in errors:
        by_stem[stem].append((variant, message))
    print(f"\n[e] {len(errors)} failure(s) across {len(by_stem)} rule(s):\n")
    for stem in sorted(by_stem):
        cases = by_stem[stem]
        print(f"  {stem}  ({len(cases)} variant(s))")
        seen = set()
        for variant, message in cases:
            if message in seen:
                continue
            seen.add(message)
            print(f"      {variant}: {message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
