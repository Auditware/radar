"""Score competing implementations of one rule against the same labelled corpus.

"Fewer findings" is not evidence. A rule that suppresses and a rule that got
more precise both report less, and telling them apart is the whole job - it is
how the regressions in #33 got through, and it is the trap in scoping a guard
per function: function scope reports *less* than per-account scope, because one
validated account excuses its unvalidated siblings. On volume alone the wrong
answer wins.

So each candidate is scored on labelled code in both directions, over every
corpus that has an opinion about this rule:

    must-fire     code that genuinely has this bug - a miss is a false negative
    must-be-quiet the same code once fixed - a hit is a false positive
    volume        real audited programs, where anything it reports is noise
                  until proven otherwise

Usage:
    python tests/compare_rule.py account_data_matching \\
        --candidate builtin_templates/account_data_matching.yaml \\
        --candidate /tmp/v2.yaml \\
        --extra-fixture /tmp/unchecked_sibling.rs:fire \\
        --extra-fixture /tmp/helper_checked_owner.rs:quiet
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))

from tests.measure import (  # noqa: E402
    VULNERABLE, FIXED, UNLABELLED,
    _located, _loc, class_mapping, corpora_root, load_templates, scan, select,
    units_corpus2, units_fixtures, units_mocks, units_production, units_sealevel,
)
from utils.ast import generate_ast_for_rust_file, generate_program_ast_for_folder  # noqa: E402
from utils.dsl.dsl import (  # noqa: E402
    inject_code_lines, process_template_outputs, wrapped_exec,
)


def _is_selected(candidate: dict, directory: Path) -> bool:
    """Would a real scan of this unit run this rule at all?

    `select()` drops a Rust template whose accent names a framework other than
    the one detected. Running every candidate directly - which this harness did
    - makes an accent change invisible: a rule locked to `stylus` measures
    identically to the same rule opened to every framework, because neither was
    ever filtered. That is how `incorrect_ceiling_division` could sit unable to
    run on a single Solana program while scoring 1.00 here.
    """
    accent = candidate.get("accent") or ""
    if not accent:
        return True
    from controller.api import detect_language_from_path

    framework = detect_language_from_path(directory if directory.is_dir() else directory.parent)[1]
    return framework == "unknown" or framework == accent


def run_rule(candidate: dict, directory: Path):
    """One rule against one unit. Errors are returned, never swallowed."""
    if not _is_selected(candidate, directory):
        # Not an error and not a silent zero: a real scan would not run this
        # rule here, and pretending otherwise is what hid the accent problem.
        return [], None
    if directory.is_dir():
        blob = generate_program_ast_for_folder(directory)
    else:
        blob = {"sources": {str(directory): generate_ast_for_rust_file(directory)},
                "metadata": {}}
    try:
        code = inject_code_lines(
            candidate["rule"], [f"ast = parse_ast({blob}, language='rust').items()"]
        )
        result = process_template_outputs(wrapped_exec(code), candidate)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return sorted(result.get("locations") or []), None


def relevant_units(stem: str, rule_name: str, root: Path, include_volume: bool = True):
    """Units that have an opinion about this rule, each with what it expects.

    A mock or fixture belongs to the rule that owns it. External corpora are
    selected by ScannerTruth's published class mapping, so a case counts only
    when the mapping says this rule is the one that claims that class. Anything
    else in those repos is volume, not a label.
    """
    mapping = class_mapping(root)
    classes = {klass for klass, rules in mapping.items() if rule_name in rules}

    chosen = []
    for unit in units_fixtures() + units_mocks():
        if unit["class"] == stem:
            chosen.append(unit)
    for unit in units_sealevel(root) + units_corpus2(root):
        from tests.measure import _normalise
        if _normalise(unit["class"] or "") in classes:
            chosen.append(unit)
    if include_volume:
        chosen.extend(units_production(root))
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem", help="template stem, e.g. account_data_matching")
    ap.add_argument("--candidate", action="append", required=True,
                    help="path to a candidate template yaml (repeatable)")
    ap.add_argument("--extra-fixture", action="append", default=[],
                    help="PATH:fire|quiet - an extra labelled case")
    ap.add_argument("--root", help="corpora root")
    ap.add_argument("--skip-volume", action="store_true",
                    help="skip the production repos (labelled corpora only, much faster)")
    ap.add_argument("--json", type=Path, help="write the full per-unit table here")
    args = ap.parse_args()

    root = corpora_root(args.root)
    candidates = []
    for path in args.candidate:
        data = yaml.safe_load(Path(path).read_text())
        candidates.append((Path(path).name + f" (v{data.get('version')})", data))

    rule_name = candidates[0][1]["name"]
    units = relevant_units(args.stem, rule_name, root, not args.skip_volume)

    for spec in args.extra_fixture:
        path, _, label = spec.rpartition(":")
        units.append({
            "corpus": "extra", "name": Path(path).name, "dir": Path(path),
            "label": VULNERABLE if label == "fire" else FIXED,
            "class": args.stem, "fix_sites": {},
        })

    print(f"rule: {rule_name}   candidates: {len(candidates)}   units: {len(units)}\n")

    table = {}
    for label, candidate in candidates:
        stats = {"tp": 0, "fp": 0, "fn": 0, "unlocated": 0, "volume": 0, "errors": 0}
        per_unit = {}
        for unit in units:
            locations, error = run_rule(candidate, unit["dir"])
            key = f"{unit['corpus']}/{unit['name']}"
            if error:
                stats["errors"] += 1
                per_unit[key] = {"error": error}
                continue
            # Firing somewhere in a vulnerable file is not detecting the bug in
            # it. Where the corpus records which lines the real fix touched, a
            # hit counts only if it lands there - otherwise a rule that reports
            # every unpack in a 1000-line file scores as a detection, and the
            # same rule reporting the same lines in the *fixed* file scores as
            # one too. `unlocated` keeps those apart without pretending they are
            # misses. Same protocol as the pack's own scorer.
            located = _located(locations, unit["fix_sites"])
            per_unit[key] = {
                "label": unit["label"], "locations": locations, "located": located,
            }
            if unit["label"] == VULNERABLE:
                if not locations:
                    stats["fn"] += 1
                elif located is False:
                    stats["unlocated"] += 1
                else:
                    stats["tp"] += 1
            elif unit["label"] == FIXED:
                if locations:
                    stats["fp"] += 1
            else:
                stats["volume"] += len(locations)
        table[label] = {"stats": stats, "units": per_unit}

    width = max(len(label) for label in table)
    print(f"{'candidate':<{width}} {'TP':>4} {'FN':>4} {'unloc':>6} {'FP':>4} {'prec':>7} "
          f"{'recall':>7} {'volume':>7} {'err':>4}")
    print("-" * (width + 50))
    for label, entry in table.items():
        s = entry["stats"]
        positives = s["tp"] + s["fp"] + s["unlocated"]
        actual = s["tp"] + s["fn"] + s["unlocated"]
        prec = "-" if not positives else f"{s['tp'] / positives:.2f}"
        rec = "-" if not actual else f"{s['tp'] / actual:.2f}"
        print(f"{label:<{width}} {s['tp']:>4} {s['fn']:>4} {s['unlocated']:>6} {s['fp']:>4} "
              f"{prec:>7} {rec:>7} {s['volume']:>7} {s['errors']:>4}")

    # --- paired "real detection" ------------------------------------------
    #
    # The metric that cannot be bought with volume. A pair counts only when the
    # rule fires at the fix site on the vulnerable variant *and* stays silent on
    # the same program once fixed. A rule that reports the same lines in both
    # has not detected the bug; it has reported the file. ScannerTruth calibrates
    # this with a control scanner that flags every line: nominally perfect,
    # really zero.
    #
    # This is what separates the two shapes of guard scoping. Function scope
    # reports more - one validated account no longer excuses its siblings only
    # because it excuses nothing - and some of that extra lands on vulnerable
    # code, which looks like recall until you check the fixed variant.
    labels = list(table)
    pairs = {}
    for unit in units:
        if unit["label"] == UNLABELLED:
            continue
        base = unit["name"].rsplit("/", 1)[0] if "/" in unit["name"] else unit["name"]
        pairs.setdefault(f"{unit['corpus']}/{base}", {})[unit["label"]] = unit

    print("\nreal detection (fires at the fix site on the bug, silent once fixed):\n")
    print(f"  {'pair':<52} " + "  ".join(f"{label[:22]:>22}" for label in labels))
    real = {label: 0 for label in labels}
    complete = 0
    for pair_name, variants in sorted(pairs.items()):
        if VULNERABLE not in variants or FIXED not in variants:
            continue
        complete += 1
        cells = []
        for label in labels:
            units_seen = table[label]["units"]
            vuln = units_seen.get(f"{variants[VULNERABLE]['corpus']}/{variants[VULNERABLE]['name']}", {})
            fixed = units_seen.get(f"{variants[FIXED]['corpus']}/{variants[FIXED]['name']}", {})
            hit = bool(vuln.get("locations")) and vuln.get("located") is not False
            quiet = not fixed.get("locations")
            if hit and quiet:
                real[label] += 1
                cells.append("detected")
            elif hit:
                cells.append("also-on-fixed")
            elif vuln.get("locations"):
                cells.append("unlocated")
            else:
                cells.append("missed")
        print(f"  {pair_name:<52} " + "  ".join(f"{c:>22}" for c in cells))

    print(f"\n  {'real detections':<52} "
          + "  ".join(f"{str(real[label]) + '/' + str(complete):>22}" for label in labels))

    print("\nper-unit disagreements (where candidates differ):\n")
    for key in sorted({k for e in table.values() for k in e["units"]}):
        rows = [table[label]["units"].get(key, {}) for label in labels]
        # Compare the locations, not just whether each candidate fired. Testing
        # `bool(locations)` hides a unit where one candidate reports one finding
        # and the other reports five, or where both report one finding in
        # different places - which is most of what a rule change actually does.
        reported = [tuple(sorted(r.get("locations") or [])) for r in rows]
        if len(set(reported)) == 1 and not any(r.get("error") for r in rows):
            continue
        unit_label = next((r.get("label") for r in rows if r.get("label")), "?")
        print(f"  {key}  [{unit_label}]")
        for label, row in zip(labels, rows):
            if row.get("error"):
                print(f"      {label:<{width}} ERROR {row['error']}")
            else:
                locs = row.get("locations") or []
                print(f"      {label:<{width}} {len(locs)} finding(s) {locs[:3]}")

    if args.json:
        args.json.write_text(json.dumps(table, indent=1))
        print(f"\n[i] full table written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
