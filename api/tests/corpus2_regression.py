"""Out-of-sample regression run against the ScannerTruth corpus-2 pack.

The two fixture gates (`test_detection_fixtures.py`, `test_noise_fixtures.py`) are
written by us, so they only ever measure what we already thought to check. This runs
the rules over seventeen real-world Solana bugs packaged by the benchmark author, each
a vulnerable/fixed pair with a pre-registered rule mapping and the fix location, and
scores them with the pack's own scorer rather than one of ours.

It is deliberately not a merge gate: the cases are someone else's mapping over public
crates, and a `missed` here is a coverage limit rather than a defect. It fails only on
a *regression* against the committed baseline - a case that scored better before.

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
from utils.ast import generate_ast_for_rust_program  # noqa: E402
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
    language, framework = detect_language_from_path(vdir)
    ast_blob = generate_ast_for_rust_program(vdir)
    findings = []
    for data in select(templates, language, framework):
        try:
            code = inject_code_lines(
                data["rule"], [f"ast = parse_ast({ast_blob}, language='rust').items()"]
            )
            result = process_template_outputs(wrapped_exec(code), data)
            if result and result.get("locations"):
                findings.append(result)
        except Exception:
            # A template that raises reports nothing, exactly as it does in a real
            # scan; the template test suite is what holds templates to working.
            pass
    return findings, len(ast_blob["sources"])


def run(pack: Path, templates):
    cases = [c["name"] for c in json.load(open(pack / "manifest.json"))["cases"]]
    results = pack / "results"
    for case in cases:
        for variant in VARIANTS:
            vdir = pack / "cases" / case / variant
            if not vdir.is_dir():
                continue
            findings, n_files = scan_variant(vdir, templates)
            leaf = results / f"{case}.{variant}"
            leaf.mkdir(parents=True, exist_ok=True)
            json.dump(findings, open(leaf / "radar.json", "w"), indent=1)
            # The pack's loader treats a missing radar.json as evidence of nothing
            # only when stdout says a scan happened.
            (leaf / "stdout.log").write_text(f"Scanned {n_files} files\n")
            print(f"  {case}.{variant:9} rules_fired={len(findings)}", flush=True)
    return results


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
        got = score(pack, run(pack, templates))

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

    for case, want, have in improvements:
        print(f"IMPROVED   {case}: {want} -> {have}")
    for case, want, have in regressions:
        print(f"REGRESSED  {case}: {want} -> {have}")

    if regressions:
        print(f"\n{len(regressions)} case(s) scored worse than the baseline.")
        return 1
    if improvements:
        print("\nNo regressions. Re-run with --update-baseline to record the gains.")
    else:
        print("\nNo change from baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
