"""Validate a template against its bad/good mocks, plus a scoping fixture.

The accuracy suite skips any template without recorded expected-line metadata,
which is most of them. This drives the same machinery directly so a rule can be
checked while it is being rewritten:

    .venv/bin/python tests/check_scoping.py [template_stem ...]

For each template it reports detections on mocks/<name>/bad (expected: at least
one) and mocks/<name>/good (expected: none). With no arguments it checks every
template that has both fixtures.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_templates import run_template_on_rust_source  # noqa: E402

TEMPLATES = Path("/api/builtin_templates")
MOCKS = Path(__file__).resolve().parent / "mocks"


def sources(directory: Path):
    return sorted(p for p in directory.rglob("*.rs"))


def check(stem: str):
    template_path = TEMPLATES / f"{stem}.yaml"
    if not template_path.exists():
        return None
    data = yaml.safe_load(template_path.read_text())

    if data.get("accent") != "anchor":
        return None

    mock = MOCKS / stem
    if not (mock / "bad").is_dir() or not (mock / "good").is_dir():
        return None
    if not sources(mock / "bad"):
        return None  # Solidity fixtures; this harness only drives the Rust path

    counts = {}
    for variant in ("bad", "good"):
        hits = []
        for source in sources(mock / variant):
            try:
                result = run_template_on_rust_source(data, source)
            except Exception as exc:  # a rule that throws is a rule that is broken
                hits.append(f"ERROR {source.name}: {exc}")
                continue
            hits.extend(result.get("locations", []))
        counts[variant] = hits

    detects = len(counts["bad"]) > 0
    clean = len(counts["good"]) == 0
    verdict = "PASS" if detects and clean else "FAIL"
    print(f"{verdict}  {data['name']}")
    print(f"        bad : {len(counts['bad'])} detection(s)" + ("" if detects else "   <-- MISSES THE BUG"))
    print(f"        good: {len(counts['good'])} detection(s)" + ("" if clean else "   <-- FALSE POSITIVE"))
    for location in counts["good"]:
        print(f"              {location}")
    return verdict == "PASS"


def main():
    stems = sys.argv[1:]
    if not stems:
        stems = sorted(p.stem for p in TEMPLATES.glob("*.yaml") if (MOCKS / p.stem).is_dir())

    results = [(stem, check(stem)) for stem in stems]
    checked = [(s, r) for s, r in results if r is not None]
    failed = [s for s, r in checked if r is False]
    print(f"\n{len(checked) - len(failed)}/{len(checked)} passed")
    if failed:
        print("failing: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
