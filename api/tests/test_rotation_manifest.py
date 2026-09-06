"""Gate: rotation cases are well-formed before anyone tries to fetch them.

Reads the manifest only - no network, no clones - so the cheapest job catches a
malformed entry. `fetch.py` does the expensive checks (that the commit resolves,
and that its fix actually touches the declared paths); this catches the cheap
mistakes that would otherwise surface as a confusing failure much later.

An empty manifest passes. That is the honest state today, and a corpus that
says it has nothing is worth more than one padded with cases that prove nothing.
"""

import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent / "rotation" / "manifest.json"
REQUIRED = ("id", "repo", "fix_commit", "class", "paths")


def _cases():
    return json.loads(MANIFEST.read_text()).get("cases", [])


def test_manifest_parses():
    assert isinstance(_cases(), list)


def test_every_case_declares_what_fetch_needs():
    problems = []
    for index, case in enumerate(_cases()):
        missing = [field for field in REQUIRED if not case.get(field)]
        if missing:
            problems.append(f"case {case.get('id', index)}: missing {missing}")
        if case.get("paths") and not isinstance(case["paths"], list):
            problems.append(f"case {case.get('id', index)}: paths must be a list")
    assert not problems, "\n  ".join(problems)


def test_case_ids_are_unique():
    ids = [c.get("id") for c in _cases()]
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicated, f"duplicate case ids: {duplicated}"
