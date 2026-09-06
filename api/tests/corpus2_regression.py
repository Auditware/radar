"""Out-of-sample regression run against the ScannerTruth corpus-2 pack.

The two fixture gates (`test_detection_fixtures.py`, `test_noise_fixtures.py`) are
written by us, so they only ever measure what we already thought to check. This runs
the rules over seventeen real-world Solana bugs packaged by the benchmark author, each
a vulnerable/fixed pair with a pre-registered rule mapping and the fix location, and
scores them with the pack's own scorer rather than one of ours.

It is deliberately not a merge gate: the cases are someone else's mapping over public
crates, and a `missed` here is a coverage limit rather than a defect. It fails only on
a *regression* against the committed baseline - a case that scored better before.

Lowering a baseline entry needs a reason, and only one reason is legitimate: the rule
was firing on the fixed variant too, so what it lost was never a detection. This
scorer reads only the vulnerable side, so it ranks `unlocated` above `missed` even
when the `unlocated` hit was carpet-bombing - `measure.py`'s paired `real` metric is
what tells the two apart. Any other downgrade is a real regression and must be fixed
rather than recorded.

Downgraded on 2026-09-06, both under that reason and both for Account Data Matching
v0.3.0: `metaplex-token-metadata` fired once on the bug and once on its fix, and
`token-2022-confidential-approve-mint` fired eighteen times on each. Neither was a
detection before and neither is a loss now; `real` stayed 1/17 across the change.

Cases already read while debugging, which are no longer out-of-sample: solend-owner-checks,
metaplex-candy-machine, anchor-account-reload-owner, solido-deposit-reserve-account,
spl-stake-pool-mint-decimals, spl-stake-pool-fee-rounding, spl-token-lending-rounding,
squads-recursive-execute. A pass on one of those is in-sample and should be reported as such.

Usage:
    python tests/corpus2_regression.py                 # clone the pack, run, compare
    python tests/corpus2_regression.py --pack DIR      # use an existing checkout
    python tests/corpus2_regression.py --update-baseline
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

API = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API))
sys.path.insert(0, str(API.parent))
sys.path.insert(0, str(API.parent / "controller"))

# `controller.api` reads these at import time; it is imported for
# `detect_language_from_path` only, so that this run selects templates by exactly the
# rule the real pipeline uses instead of a copy that can drift from it. The values are
# never used - nothing here talks to the API.
os.environ.setdefault("DJANGO_PORT", "8000")
os.environ.setdefault("DJANGO_HOST", "api")
os.environ.setdefault("DJANGO_HOST_LOCAL", "localhost")

from controller.api import detect_language_from_path  # noqa: E402
from utils.ast import generate_program_ast_for_folder  # noqa: E402
from utils.dsl.dsl import (  # noqa: E402
    inject_code_lines,
    process_template_outputs,
    wrapped_exec,
)

PACK_REPO = "https://github.com/halobartku/scannertruth.git"
# Pinned: the pack is upstream's to change, and an unpinned clone would turn their
# edits into our CI failures.
PACK_COMMIT = "0c48dd888854e5545ff6babef2c68f31b3a2f35f"
PACK_SUBDIR = "regression-pack-radar"

BASELINE = Path(__file__).resolve().parent / "corpus2_baseline.json"
VARIANTS = ("insecure", "secure")

# Worse verdicts sort lower. `no-rule` sits under `missed` on purpose: a case that
# drops from `missed` to `no-rule` means a mapped rule name stopped existing, which is
# a rename or deletion we want to hear about.
RANK = {"not-run": -1, "no-rule": 0, "missed": 1, "unlocated": 2, "detected": 3}


def clone_pack(dest: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", PACK_REPO], check=True)
    subprocess.run(
        ["git", "-C", str(dest), "fetch", "-q", "--depth", "1", "origin", PACK_COMMIT],
        check=True,
    )
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)
    return dest / PACK_SUBDIR


def load_templates():
    out = []
    for path in sorted((API / "builtin_templates").glob("*.yaml")):
        data = yaml.safe_load(open(path))
        if data:
            out.append(data)
    return out


def select(templates, language, framework):
    """The template filter from api/views.py, applied to one variant directory."""
    chosen = []
    for data in templates:
        if data.get("language", "rust") != language:
            continue
        accent = data.get("accent", "")
        if language == "rust" and accent and framework != "unknown" and accent != framework:
            continue
        chosen.append(data)
    return chosen


def scan_variant(vdir: Path, templates):
    _, framework = detect_language_from_path(vdir)
    # Language the way `views.py` decides it, so a crate with no Cargo.toml is
    # still scanned as Rust rather than selecting no templates at all.
    language = "solidity" if next(vdir.rglob("*.sol"), None) else "rust"
    ast_blob = generate_program_ast_for_folder(vdir)
    findings, errors = [], []
    for data in select(templates, language, framework):
        try:
            code = inject_code_lines(
                data["rule"], [f"ast = parse_ast({ast_blob}, language='rust').items()"]
            )
            result = process_template_outputs(wrapped_exec(code), data)
            if result and result.get("locations"):
                findings.append(result)
        except Exception as exc:
            # A template that raises reports nothing. It used to do so silently
            # here, which meant a rule that broke and a rule that found nothing
            # produced the same corpus verdict - the exact confusion `RuleSkip`
            # was introduced to end. Record it and let the run say so.
            errors.append(f"{data['name']}: {type(exc).__name__}: {exc}")
    return findings, len(ast_blob["sources"]), errors


# Rules that raised during the run. A verdict computed while errors were
# invisible would read "this rule does not detect this bug" when the truth is
# "this rule crashed", and those call for opposite fixes.
rule_errors = []


def run(pack: Path, templates):
    cases = [c["name"] for c in json.load(open(pack / "manifest.json"))["cases"]]
    results = pack / "results"
    for case in cases:
        for variant in VARIANTS:
            vdir = pack / "cases" / case / variant
            if not vdir.is_dir():
                continue
            findings, n_files, errors = scan_variant(vdir, templates)
            rule_errors.extend(f"{case}.{variant}: {e}" for e in errors)
            leaf = results / f"{case}.{variant}"
            leaf.mkdir(parents=True, exist_ok=True)
            json.dump(findings, open(leaf / "radar.json", "w"), indent=1)
            # The pack's loader treats a missing radar.json as evidence of nothing
            # only when stdout says a scan happened.
            (leaf / "stdout.log").write_text(f"Scanned {n_files} files\n")
            suffix = f" errors={len(errors)}" if errors else ""
            print(f"  {case}.{variant:9} rules_fired={len(findings)}{suffix}", flush=True)
    return results


LOCAL_MAPPING = Path(__file__).resolve().parent / "corpus2_mapping_local.json"


def _shadow_pack(pack: Path, tmp: Path) -> Path:
    """A view of the pack whose `mapping.json` also knows our newer rules.

    `check.py` reads `mapping.json` from its own directory and takes no override,
    and the pack's copy predates every rule added since it was written - so those
    classes score `no-rule` forever and the regression under-reports coverage
    radar actually has. Everything is symlinked except the mapping, so the real
    checkout is never written to and the scorer still runs unmodified.
    """
    if not LOCAL_MAPPING.is_file():
        return pack

    shadow = tmp / "pack"
    shadow.mkdir(parents=True, exist_ok=True)
    for entry in pack.iterdir():
        if entry.name != "mapping.json":
            link = shadow / entry.name
            if not link.exists():
                link.symlink_to(entry)

    merged = json.load(open(pack / "mapping.json"))
    additions = json.load(open(LOCAL_MAPPING)).get("map", {})
    # The pack's own entries win: this file adds coverage, it never reinterprets
    # a class the benchmark author has already mapped.
    for klass, rules in additions.items():
        merged["map"].setdefault(klass, rules)
    (shadow / "mapping.json").write_text(json.dumps(merged, indent=1))
    return shadow


def score(pack: Path, results: Path):
    """Verdicts come from the pack's own scorer, run unmodified."""
    out = pack / "verdicts.json"
    subprocess.run(
        [sys.executable, "check.py", "--results", str(results), "--json", str(out)],
        cwd=pack,
        check=True,
    )
    return {r["id"]: r["verdict"] for r in json.load(open(out))["cases"]}


def compare(got, baseline):
    regressions, improvements = [], []
    for case, want in sorted(baseline.items()):
        have = got.get(case, "not-run")
        if have == want:
            continue
        (regressions if RANK[have] < RANK[want] else improvements).append((case, want, have))
    for case in sorted(set(got) - set(baseline)):
        improvements.append((case, "(new case)", got[case]))
    return regressions, improvements


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", help="existing scannertruth checkout or pack directory")
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        if args.pack:
            pack = Path(args.pack)
            if (pack / PACK_SUBDIR).is_dir():
                pack = pack / PACK_SUBDIR
        else:
            print(f"cloning pack at {PACK_COMMIT[:9]}", flush=True)
            pack = clone_pack(Path(tmp) / "scannertruth")

        templates = load_templates()
        print(f"{len(templates)} templates, pack at {pack}", flush=True)
        results = run(pack, templates)
        got = score(_shadow_pack(pack, Path(tmp)), results)

    if args.update_baseline:
        BASELINE.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n")
        print(f"\nbaseline written: {BASELINE}")
        return 0

    baseline = json.loads(BASELINE.read_text())
    regressions, improvements = compare(got, baseline)

    tally = {}
    for verdict in got.values():
        tally[verdict] = tally.get(verdict, 0) + 1
    print("\n" + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))

    if rule_errors:
        # Printed before the verdicts, because a verdict computed while a rule
        # was raising is not the verdict it looks like: "missed" here can mean
        # "crashed", and those need opposite fixes.
        print(f"\n{len(rule_errors)} rule error(s) during the run - verdicts for "
              f"these rules are not measurements of detection:")
        for entry in sorted(set(rule_errors)):
            print(f"  {entry}")

    for case, want, have in improvements:
        print(f"IMPROVED   {case}: {want} -> {have}")
    for case, want, have in regressions:
        print(f"REGRESSED  {case}: {want} -> {have}")

    if regressions:
        print(f"\n{len(regressions)} case(s) scored worse than the baseline.")
        return 1
    if rule_errors:
        print(f"\n{len(set(rule_errors))} rule(s) raised. No verdict regressed, but "
              f"a raising rule reports nothing, so the score understates nothing "
              f"and overstates the rules' health.")
        return 1
    if improvements:
        print("\nNo regressions. Re-run with --update-baseline to record the gains.")
    else:
        print("\nNo change from baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
