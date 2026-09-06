"""Before/after measurement for rule and engine changes.

Every accuracy gate in this repo answers "did this break something we already
thought of". None of them answers "is this change better", and that question is
not the same one: a rule can get quieter on every corpus we own and still be
worse, because suppression and precision look identical when you only count.

This measures a change on three axes at once, over labelled corpora, and refuses
to reduce them to a single number:

  recall     - does the rule still fire on code that is genuinely vulnerable
  precision  - does it stay silent on the same code once fixed
  volume     - how much it reports per KLOC of ordinary production code

A change is an improvement only when precision rises and recall does not fall
(or the mirror). A drop in volume on its own is not evidence of anything - it is
what suppression looks like too, which is the failure mode #23 and #33 both hit.

Corpora, by how much they can be trusted:

  fixtures    in-repo, per-rule, hand-labelled both directions (detection_fixtures
              must fire, noise_fixtures must stay silent). In-sample by
              construction - written by whoever wrote the rule.
  mocks       in-repo, per-rule bad/good pairs. In-sample, same caveat.
  sealevel    sealevel-attacks. Class-labelled, insecure vs secure/recommended.
              Radar has been tuned against it, so treat recall here as in-sample
              and only the `secure`/`recommended` side as informative.
  corpus2     ScannerTruth's regression pack: seventeen real-world bugs with
              pre-registered rule mappings and the lines the real fix touched.
              The only out-of-sample recall signal we have. Never tune against it.
  production  real audited programs with no deliberate bugs. Unlabelled, so it
              measures volume only - the denominator issue #32 is about.

Usage:
    python tests/measure.py snapshot --out before.json
    # change something
    python tests/measure.py snapshot --out after.json
    python tests/measure.py compare before.json after.json
    python tests/measure.py compare before.json after.json --rule "Account Data Matching"

Corpora live outside the repo (they are other people's code). Point `--root` at a
directory holding the checkouts, or set RADAR_CORPORA. `python tests/measure.py
corpora` prints what is expected and what is present.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

API = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(API))
sys.path.insert(0, str(API.parent))
sys.path.insert(0, str(API.parent / "controller"))

# `controller.api` reads these at import time; it is imported for
# `detect_language_from_path` only, so the corpora are selected by exactly the
# rule the real pipeline uses rather than a copy that can drift from it.
os.environ.setdefault("DJANGO_PORT", "8000")
os.environ.setdefault("DJANGO_HOST", "api")
os.environ.setdefault("DJANGO_HOST_LOCAL", "localhost")

from controller.api import detect_language_from_path  # noqa: E402
from utils.ast import (  # noqa: E402
    generate_ast_for_rust_file,
    generate_program_ast_for_folder,
)
from utils.dsl.dsl import (  # noqa: E402
    inject_code_lines,
    process_template_outputs,
    wrapped_exec,
)

TEMPLATES = API / "builtin_templates"

# External checkouts. Pinned where the corpus is a measurement instrument; the
# production repos are volume denominators, where an exact revision matters less
# than that before/after used the same one - which the snapshot records.
EXTERNAL = {
    "sealevel": ("https://github.com/coral-xyz/sealevel-attacks.git", None),
    "scannertruth": ("https://github.com/halobartku/scannertruth.git",
                     "0c48dd888854e5545ff6babef2c68f31b3a2f35f"),
    "spl-token": ("https://github.com/solana-program/token.git", None),
    "spl-stake-pool": ("https://github.com/solana-program/stake-pool.git", None),
    "anchor": ("https://github.com/coral-xyz/anchor.git", None),
}

VULNERABLE, FIXED, UNLABELLED = "vulnerable", "fixed", "unlabelled"


# --- corpus discovery --------------------------------------------------------

def _loc(directory: Path) -> int:
    """Non-blank, non-comment Rust lines. The volume denominator."""
    total = 0
    for path in directory.rglob("*.rs"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("//"):
                total += 1
    return total


def _unit(corpus, name, directory, label, klass=None, fix_sites=None):
    return {
        "corpus": corpus,
        "name": name,
        "dir": directory,
        "label": label,
        "class": klass,
        "fix_sites": fix_sites or {},
    }


def _expected_mock_lines():
    """The accuracy suite's recorded expectations, as fix sites per mock folder.

    Without these, a mock scores as detected whenever the rule fires *anywhere*
    in the file - so a rule that stops finding the planted bug and starts
    reporting something else entirely still reads as a detection. That is the
    same presence-vs-location confusion the corpus scorer already avoids; the
    mocks had the ground truth recorded all along, in another file.

    Column precision stays with `test_template_accuracy`. This is line-level,
    which is what the located check needs.
    """
    try:
        from tests.test_templates import EXPECTED_DETECTIONS
    except Exception:
        return {}

    per_folder = {}
    for expected in EXPECTED_DETECTIONS.values():
        for location in expected.get("bad") or []:
            path, _, rest = location.partition(".rs:")
            if not rest:
                continue
            line = rest.split(":")[0]
            if not line.isdigit():
                continue
            source = f"{path}.rs"
            parts = Path(source).parts
            if "mocks" not in parts:
                continue
            index = parts.index("mocks")
            folder = "/".join(parts[index + 1:index + 3])       # <stem>/bad
            relative = "/".join(parts[index + 3:])              # src/lib.rs
            per_folder.setdefault(folder, {}).setdefault(relative, []).append(int(line))
    return per_folder


def units_mocks():
    """bad/ and good/ under tests/mocks, labelled by the rule that owns them."""
    expected = _expected_mock_lines()
    found = []
    for variant_dir in sorted((TESTS / "mocks").glob("*/*")):
        if variant_dir.name not in ("bad", "good") or not list(variant_dir.rglob("*.rs")):
            continue
        stem = variant_dir.parent.name
        label = VULNERABLE if variant_dir.name == "bad" else FIXED
        found.append(_unit(
            "mocks", f"{stem}/{variant_dir.name}", variant_dir, label, klass=stem,
            fix_sites=expected.get(f"{stem}/{variant_dir.name}", {}) if label == VULNERABLE else {},
        ))
    return found


def units_fixtures():
    """detection_fixtures must fire, noise_fixtures must stay silent.

    Each file is its own unit; the rule it belongs to is the part of the filename
    before `__`, which is how both fixture gates already resolve it.
    """
    found = []
    for kind, label in (("detection_fixtures", VULNERABLE), ("noise_fixtures", FIXED)):
        for fixture in sorted((TESTS / kind).glob("*.rs")):
            found.append(_unit("fixtures", f"{kind}/{fixture.name}", fixture,
                               label, klass=fixture.name.split("__")[0]))
    return found


def units_sealevel(root: Path):
    base = root / "sealevel" / "programs"
    if not base.is_dir():
        return []
    found = []
    for program in sorted(base.iterdir()):
        if not program.is_dir():
            continue
        for variant in ("insecure", "secure", "recommended"):
            vdir = program / variant
            if not (vdir / "src").is_dir():
                continue
            label = VULNERABLE if variant == "insecure" else FIXED
            found.append(_unit("sealevel", f"{program.name}/{variant}", vdir, label,
                               klass=program.name))
    return found


def units_corpus2(root: Path):
    """The pack ships `expected.json` with the lines each real fix touched."""
    pack = root / "scannertruth" / "regression-pack-radar"
    if not pack.is_dir():
        return []
    expected = {c["id"]: c for c in json.load(open(pack / "expected.json"))["cases"]}
    found = []
    for case in json.load(open(pack / "manifest.json"))["cases"]:
        meta = expected.get(case["name"], {})
        for variant in ("insecure", "secure"):
            vdir = pack / "cases" / case["name"] / variant
            if not vdir.is_dir():
                continue
            label = VULNERABLE if variant == "insecure" else FIXED
            found.append(_unit("corpus2", f"{case['name']}/{variant}", vdir, label,
                               klass=case["class"],
                               fix_sites=meta.get("fix_sites", {}) if label == VULNERABLE else {}))
    return found


def units_production(root: Path):
    """Audited programs with no planted bugs. Volume only - nothing is labelled."""
    targets = [
        ("spl-token", root / "spl-token" / "program" / "src"),
        ("spl-token-interface", root / "spl-token" / "interface" / "src"),
        ("spl-stake-pool", root / "spl-stake-pool" / "program" / "src"),
    ]
    anchor_tests = root / "anchor" / "tests"
    if anchor_tests.is_dir():
        for program in sorted(anchor_tests.glob("*/programs/*")):
            if (program / "src").is_dir():
                targets.append((f"anchor/{program.parent.parent.name}/{program.name}", program))
    return [_unit("production", name, path, UNLABELLED)
            for name, path in targets if path.is_dir()]


def all_units(root: Path, corpora=None):
    builders = {
        "fixtures": lambda: units_fixtures(),
        "mocks": lambda: units_mocks(),
        "sealevel": lambda: units_sealevel(root),
        "corpus2": lambda: units_corpus2(root),
        "production": lambda: units_production(root),
    }
    chosen = corpora or list(builders)
    found = []
    for name in chosen:
        found.extend(builders[name]())
    return found


# --- scanning ----------------------------------------------------------------

def load_templates():
    out = []
    for path in sorted(TEMPLATES.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if data and "rule" in data:
            out.append(data)
    return out


def select(templates, language, framework):
    """The template filter from api/views.py, applied to one directory."""
    chosen = []
    for data in templates:
        if data.get("language", "rust") != language:
            continue
        accent = data.get("accent", "")
        if language == "rust" and accent and framework != "unknown" and accent != framework:
            continue
        chosen.append(data)
    return chosen


def scan(directory: Path, templates):
    """Findings keyed by rule name, plus any rule that raised.

    A rule that raises is recorded, not swallowed. Measuring a change while
    errors are invisible is how a rule that broke gets read as a rule that got
    quieter - which is the whole failure this file exists to make visible.
    """
    # Exactly what the pipeline does, split the way the pipeline splits it:
    # `views.py` decides the language itself (Rust unless there are `.sol`
    # files), and only the framework comes from the controller's detection. A
    # harness that took both from the controller would silently select no
    # templates at all for a folder of `.rs` files with no Cargo.toml, and
    # report it as a rule that missed.
    _, framework = detect_language_from_path(directory)
    haystack = directory.parent if directory.is_file() else directory
    language = "solidity" if next(haystack.rglob("*.sol"), None) else "rust"
    if directory.is_dir():
        ast_blob = generate_program_ast_for_folder(directory)
        n_sources = len(ast_blob["sources"])
    else:
        # A lone fixture file, scanned the way `generate_ast/` scans a file.
        ast_blob = {"sources": {str(directory): generate_ast_for_rust_file(directory)},
                    "metadata": {}}
        n_sources = 1
    unparsed = ast_blob.get("metadata", {}).get("unparsed_sources") or []
    findings, errors = {}, {}
    if unparsed:
        errors["(parser)"] = f"{len(unparsed)} source(s) could not be parsed"
    for data in select(templates, language, framework):
        try:
            code = inject_code_lines(
                data["rule"], [f"ast = parse_ast({ast_blob}, language='rust').items()"]
            )
            result = process_template_outputs(wrapped_exec(code), data)
        except Exception as exc:
            errors[data["name"]] = f"{type(exc).__name__}: {exc}"
            continue
        locations = result.get("locations") if result else None
        if locations:
            findings[data["name"]] = sorted(locations)
    return findings, errors, n_sources


def git_revision(path: Path):
    if not path.is_dir():
        return None
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def snapshot(root: Path, corpora=None):
    templates = load_templates()
    units = all_units(root, corpora)
    out = {
        "meta": {
            "radar_revision": git_revision(API.parent),
            "corpora_revisions": {n: git_revision(root / n) for n in EXTERNAL},
            "template_count": len(templates),
        },
        "units": {},
    }
    for i, unit in enumerate(units, 1):
        directory = unit["dir"]
        try:
            findings, errors, n_files = scan(directory, templates)
        except Exception as exc:
            # One unit that cannot be scanned must not cost the whole snapshot.
            # It is recorded as an error rather than dropped, so a corpus that
            # shrank says so instead of quietly measuring less.
            findings, errors, n_files = {}, {"(scan)": f"{type(exc).__name__}: {exc}"}, 0
        key = f"{unit['corpus']}/{unit['name']}"
        out["units"][key] = {
            "corpus": unit["corpus"],
            "label": unit["label"],
            "class": unit["class"],
            "fix_sites": unit["fix_sites"],
            "loc": _loc(directory) if directory.is_dir() else _loc(directory.parent),
            "files": n_files,
            "findings": findings,
            "errors": errors,
        }
        print(f"  [{i:3d}/{len(units)}] {key:60s} rules={len(findings):3d} errors={len(errors)}",
              flush=True)
    return out

# --- scoring -----------------------------------------------------------------

TOLERANCE = 3  # lines either side of a fix site; the pack's scorer uses the same


def _normalise(name):
    """Corpus 1 names classes `10-sysvar-address-checking`, corpus 2 drops the number."""
    head, _, rest = name.partition("-")
    return rest if head.isdigit() and rest else name


def class_mapping(root: Path):
    """class -> {rule names}, from ScannerTruth's published mapping for radar.

    Using their mapping rather than one of ours is the point: it was derived from
    radar's own rule names, and if it is wrong that is a correction to publish,
    not a number to quietly adjust.
    """
    path = root / "scannertruth" / "regression-pack-radar" / "mapping.json"
    if not path.is_file():
        return {}
    raw = json.load(open(path)).get("map", {})
    return {_normalise(k): set(v) for k, v in raw.items()}


def rule_names_by_stem():
    """mock/fixture folder name -> rule name.

    Registered under both the template stem and the normalised display name,
    the same two-step resolution `get_template_test_data` uses. Several mock
    folders are named after the rule's display name rather than its file
    (`arbitrary_cross_program_invocation` for `arbitrary_cpi.yaml`), and
    resolving by stem alone reported those as rules that do not exist - which
    reads as a coverage gap when it is a naming one.
    """
    out = {}
    for path in sorted(TEMPLATES.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if not data or "name" not in data:
            continue
        out[path.stem] = data["name"]
        normalised = re.sub(r"[^a-z0-9]+", "_", data["name"].lower()).strip("_")
        out.setdefault(normalised, data["name"])
    return out


def _line_of(location):
    """`path/to/file.rs:LINE:col-col` -> (file, line)."""
    parts = location.rsplit(":", 2)
    if len(parts) != 3:
        return location, None
    try:
        return parts[0], int(parts[1])
    except ValueError:
        return parts[0], None


def _located(locations, fix_sites):
    """Does any finding land on or near a line the real fix touched?"""
    if not fix_sites:
        return None  # no ground truth for this unit; presence is all we can judge
    for location in locations:
        path, line = _line_of(location)
        if line is None:
            continue
        for site_file, lines in fix_sites.items():
            if path.endswith(site_file) or site_file.endswith(Path(path).name):
                if any(abs(line - want) <= TOLERANCE for want in lines):
                    return True
    return False


def rules_for_unit(unit, mapping, by_stem):
    """The rules whose job it is to catch this unit's bug.

    For in-repo corpora that is the rule that owns the fixture. For the external
    corpora it is the published class mapping - which is what keeps a tool from
    scoring a hit because some unrelated rule happened to fire in the file.
    """
    klass = unit.get("class")
    if not klass:
        return set()
    if unit["corpus"] in ("mocks", "fixtures"):
        name = by_stem.get(klass)
        return {name} if name else set()
    return mapping.get(_normalise(klass), set())


def score(snap, root: Path):
    mapping = class_mapping(root)
    by_stem = rule_names_by_stem()

    per_corpus = defaultdict(lambda: {
        "tp": 0, "fp": 0, "fn": 0, "unlocated": 0, "no_rule": 0,
        "units": 0, "loc": 0, "findings": 0, "findings_on_fixed": 0, "errors": 0,
    })
    per_rule = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "findings": 0})
    cases = {}

    for key, unit in snap["units"].items():
        bucket = per_corpus[unit["corpus"]]
        bucket["units"] += 1
        bucket["loc"] += unit["loc"]
        bucket["errors"] += len(unit.get("errors", {}))
        total = sum(len(v) for v in unit["findings"].values())
        bucket["findings"] += total
        if unit["label"] == FIXED:
            bucket["findings_on_fixed"] += total

        for rule, locations in unit["findings"].items():
            per_rule[rule]["findings"] += len(locations)

        if unit["label"] == UNLABELLED:
            continue

        wanted = rules_for_unit(unit, mapping, by_stem)
        if not wanted:
            if unit["label"] == VULNERABLE:
                bucket["no_rule"] += 1
                cases[key] = "no-rule"
            continue

        hits = [loc for rule in wanted for loc in unit["findings"].get(rule, [])]
        if unit["label"] == VULNERABLE:
            if not hits:
                bucket["fn"] += 1
                cases[key] = "missed"
            elif _located(hits, unit["fix_sites"]) is False:
                bucket["unlocated"] += 1
                cases[key] = "unlocated"
            else:
                bucket["tp"] += 1
                cases[key] = "detected"
            for rule in wanted:
                if unit["findings"].get(rule):
                    per_rule[rule]["tp"] += 1
                else:
                    per_rule[rule]["fn"] += 1
        else:
            if hits:
                bucket["fp"] += 1
                cases[key] = "false-positive"
                for rule in wanted:
                    if unit["findings"].get(rule):
                        per_rule[rule]["fp"] += 1
            else:
                cases[key] = "clean"

    # --- paired "real detection" ---------------------------------------------
    #
    # `recall` above counts a hit on the vulnerable variant without asking what
    # the same rule did to the fixed one. That is generous in exactly the way a
    # benchmark must not be: a rule reporting every unpack in a 1000-line file
    # scores a detection, and scores it again on the file after the fix. This
    # counts a pair only when the rule fires at the fix site on the bug *and*
    # goes quiet once it is fixed - the metric a scanner cannot buy with volume,
    # and the one ScannerTruth calibrates with a flag-everything control.
    pairs = defaultdict(dict)
    for key, unit in snap["units"].items():
        if unit["label"] == UNLABELLED:
            continue
        base = key.rsplit("/", 1)[0]
        pairs[base][unit["label"]] = (key, unit)

    for base, variants in pairs.items():
        if VULNERABLE not in variants or FIXED not in variants:
            continue
        vuln_key, vuln = variants[VULNERABLE]
        _, fixed = variants[FIXED]
        bucket = per_corpus[vuln["corpus"]]
        bucket["pairs"] = bucket.get("pairs", 0) + 1
        if cases.get(vuln_key) != "detected":
            continue
        wanted = rules_for_unit(vuln, mapping, by_stem)
        if any(fixed["findings"].get(rule) for rule in wanted):
            # Fired on the bug and on its fix. Not a detection.
            bucket["also_on_fixed"] = bucket.get("also_on_fixed", 0) + 1
            continue
        bucket["real"] = bucket.get("real", 0) + 1

    def ratio(num, den):
        return None if den == 0 else round(num / den, 4)

    for bucket in per_corpus.values():
        bucket.setdefault("pairs", 0)
        bucket.setdefault("real", 0)
        bucket.setdefault("also_on_fixed", 0)
        bucket["precision"] = ratio(bucket["tp"], bucket["tp"] + bucket["fp"])
        bucket["recall"] = ratio(bucket["tp"], bucket["tp"] + bucket["fn"] + bucket["unlocated"])
        bucket["real_recall"] = ratio(bucket["real"], bucket["pairs"])
        bucket["per_kloc"] = ratio(bucket["findings"] * 1000, bucket["loc"])
    for stats in per_rule.values():
        stats["precision"] = ratio(stats["tp"], stats["tp"] + stats["fp"])
        stats["recall"] = ratio(stats["tp"], stats["tp"] + stats["fn"])

    return {"corpora": dict(per_corpus), "rules": dict(per_rule), "cases": cases}


# --- reporting ---------------------------------------------------------------

def print_score(scored):
    print(f"\n{'corpus':<12} {'units':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'unloc':>6} "
          f"{'norule':>7} {'prec':>6} {'recall':>7} {'real':>9} {'finds':>7} {'/KLOC':>7} {'err':>4}")
    print("-" * 104)
    for name in sorted(scored["corpora"]):
        c = scored["corpora"][name]
        def fmt(value, spec=">6"):
            return format("-" if value is None else f"{value:.2f}", spec)
        real = f"{c['real']}/{c['pairs']}" if c["pairs"] else "-"
        print(f"{name:<12} {c['units']:>6} {c['tp']:>4} {c['fp']:>4} {c['fn']:>4} "
              f"{c['unlocated']:>6} {c['no_rule']:>7} {fmt(c['precision'])} "
              f"{fmt(c['recall'], '>7')} {real:>9} {c['findings']:>7} "
              f"{fmt(c['per_kloc'], '>7')} {c['errors']:>4}")
    also = sum(c["also_on_fixed"] for c in scored["corpora"].values())
    if also:
        print(f"\n  {also} pair(s) counted as detected by `recall` fire on the fixed "
              f"variant too, and are excluded from `real`.")
    total_fixed = sum(c["findings_on_fixed"] for c in scored["corpora"].values())
    total = sum(c["findings"] for c in scored["corpora"].values())
    if total:
        print(f"\n  findings landing on already-fixed code: {total_fixed}/{total} "
              f"({100 * total_fixed / total:.0f}%)")


def compare(before, after, root: Path, rule_filter=None):
    """Per-rule deltas with the specific locations behind them.

    Aggregates are what people quote; the location lists are what make a claim
    checkable. Both are printed, and the verdict is deliberately conservative -
    anything that trades recall for precision is reported as MIXED for a human
    to judge, not scored as a win.
    """
    s_before, s_after = score(before, root), score(after, root)

    print("=" * 92)
    print("BEFORE");  print_score(s_before)
    print("\n" + "=" * 92)
    print("AFTER");   print_score(s_after)

    print("\n" + "=" * 92)
    print("PER-RULE CHANGES\n")
    rules = sorted(set(s_before["rules"]) | set(s_after["rules"]))
    changed = 0
    for rule in rules:
        if rule_filter and rule_filter.lower() not in rule.lower():
            continue
        b = s_before["rules"].get(rule, {"tp": 0, "fp": 0, "fn": 0, "findings": 0})
        a = s_after["rules"].get(rule, {"tp": 0, "fp": 0, "fn": 0, "findings": 0})
        if all(b.get(k) == a.get(k) for k in ("tp", "fp", "fn", "findings")):
            continue
        changed += 1
        d_tp, d_fp, d_fn = a["tp"] - b["tp"], a["fp"] - b["fp"], a["fn"] - b["fn"]
        if d_fn > 0 or d_tp < 0:
            verdict = "REGRESSION" if d_fp >= 0 else "MIXED"
        elif d_fp < 0 or d_tp > 0:
            verdict = "IMPROVEMENT" if d_fn <= 0 and d_tp >= 0 else "MIXED"
        else:
            verdict = "NEUTRAL"
        print(f"  {verdict:<12} {rule}")
        print(f"      TP {b['tp']:>3} -> {a['tp']:<3} ({d_tp:+d})   "
              f"FP {b['fp']:>3} -> {a['fp']:<3} ({d_fp:+d})   "
              f"FN {b['fn']:>3} -> {a['fn']:<3} ({d_fn:+d})   "
              f"findings {b['findings']} -> {a['findings']}")

    if not changed:
        print("  (no rule changed on any axis)")

    print("\n" + "=" * 92)
    print("CASE VERDICT CHANGES\n")
    moved = 0
    for key in sorted(set(s_before["cases"]) | set(s_after["cases"])):
        was, now = s_before["cases"].get(key, "-"), s_after["cases"].get(key, "-")
        if was != now:
            moved += 1
            print(f"  {key:<58} {was:>14} -> {now}")
    if not moved:
        print("  (no case changed verdict)")

    print("\n" + "=" * 92)
    print("LOCATION-LEVEL DIFF\n")
    for key in sorted(set(before["units"]) | set(after["units"])):
        b_unit = before["units"].get(key, {"findings": {}, "label": "-"})
        a_unit = after["units"].get(key, {"findings": {}, "label": "-"})
        for rule in sorted(set(b_unit["findings"]) | set(a_unit["findings"])):
            if rule_filter and rule_filter.lower() not in rule.lower():
                continue
            was, now = set(b_unit["findings"].get(rule, [])), set(a_unit["findings"].get(rule, []))
            added, removed = sorted(now - was), sorted(was - now)
            if not added and not removed:
                continue
            print(f"  {key}  [{a_unit.get('label', b_unit.get('label'))}]  {rule}")
            for location in added:
                print(f"      + {location}")
            for location in removed:
                print(f"      - {location}")

    errors = {k: u["errors"] for k, u in after["units"].items() if u.get("errors")}
    if errors:
        print("\n" + "=" * 92)
        print("RULES THAT RAISED (findings from these are missing, not absent)\n")
        for key, per_rule in sorted(errors.items()):
            for rule, message in sorted(per_rule.items()):
                print(f"  {key}: {rule}: {message}")


# --- cli ---------------------------------------------------------------------

def corpora_root(arg=None) -> Path:
    return Path(arg or os.environ.get("RADAR_CORPORA") or (TESTS / ".corpora")).expanduser()


def cmd_corpora(root: Path):
    print(f"corpora root: {root}\n")
    for name, (url, pin) in EXTERNAL.items():
        path = root / name
        state = git_revision(path) if path.is_dir() else "MISSING"
        print(f"  {name:<16} {state or 'no-git':<10} {url}" + (f"  @{pin[:12]}" if pin else ""))
    print("\nfetch with:")
    print(f"  mkdir -p {root}")
    for name, (url, pin) in EXTERNAL.items():
        if pin:
            print(f"  git clone --filter=blob:none {url} {root / name} && "
                  f"git -C {root / name} checkout {pin}")
        else:
            print(f"  git clone --depth 1 {url} {root / name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="directory holding the corpus checkouts")
    sub = parser.add_subparsers(dest="command", required=True)

    p_snap = sub.add_parser("snapshot", help="scan every corpus and record findings")
    p_snap.add_argument("--out", type=Path, required=True)
    p_snap.add_argument("--corpora", help="comma-separated subset")

    p_score = sub.add_parser("score", help="score one snapshot")
    p_score.add_argument("snapshot", type=Path)

    p_cmp = sub.add_parser("compare", help="score two snapshots and diff them")
    p_cmp.add_argument("before", type=Path)
    p_cmp.add_argument("after", type=Path)
    p_cmp.add_argument("--rule", help="restrict per-rule and location output to this rule")

    sub.add_parser("corpora", help="show which corpora are present")

    args = parser.parse_args()
    root = corpora_root(args.root)

    if args.command == "corpora":
        cmd_corpora(root)
        return 0

    if args.command == "snapshot":
        chosen = args.corpora.split(",") if args.corpora else None
        snap = snapshot(root, chosen)
        args.out.write_text(json.dumps(snap, indent=1))
        print(f"\n[i] snapshot written to {args.out}")
        print_score(score(snap, root))
        return 0

    if args.command == "score":
        print_score(score(json.loads(args.snapshot.read_text()), root))
        return 0

    compare(json.loads(args.before.read_text()),
            json.loads(args.after.read_text()), root, args.rule)
    return 0


if __name__ == "__main__":
    sys.exit(main())
