"""Materialise rotation cases from their fix commits.

A case is a repository and the commit that fixed a bug. This checks out that
commit and its parent into `secure/` and `insecure/`, and derives the fix sites
from the diff between them.

Deriving the sites rather than recording them by hand is the point: adding a
case means writing down a repo, a commit and a class, and never opening the
diff. What a person cannot avoid learning is roughly what the case is about,
which is why the person who adds cases should not be the person who then writes
rules for those classes. See README.md.

    python tests/rotation/fetch.py --out /some/dir
    python tests/rotation/fetch.py --out /some/dir --only <case id>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"


def _git(*args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check,
                          capture_output=True, text=True).stdout.strip()


def _clone(repo: str, dest: Path):
    if dest.is_dir():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  cloning {repo}", flush=True)
    _git("clone", "--quiet", "--filter=blob:none", repo, str(dest))
    return dest


def _worktree(mirror: Path, commit: str, dest: Path):
    if dest.is_dir():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    _git("worktree", "add", "--detach", "--force", str(dest), commit, cwd=mirror)


def fix_sites(mirror: Path, commit: str, paths):
    """Lines in the *vulnerable* file that the fix changed, per file.

    Same convention the ScannerTruth scorer uses: a finding counts as located
    only if it lands near one of these, so a rule that reports every line of a
    long file cannot score a detection by volume.
    """
    parent = _git("rev-parse", f"{commit}^", cwd=mirror)
    diff = _git("diff", "--unified=0", parent, commit, "--", *paths, cwd=mirror)

    sites, current = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            if line.startswith("--- a/"):
                current = line[len("--- a/"):]
            continue
        if line.startswith("@@") and current:
            # @@ -old,count +new,count @@ - the old side is the vulnerable file.
            old = line.split(" ")[1].lstrip("-")
            start, _, count = old.partition(",")
            if start.isdigit():
                span = int(count) if count.isdigit() else 1
                sites.setdefault(current, []).extend(
                    range(int(start), int(start) + max(span, 1))
                )
    return sites


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    cases = [c for c in manifest["cases"] if not args.only or c["id"] == args.only]
    if not cases:
        print("[e] no cases matched")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    expected = {"cases": []}

    for case in cases:
        print(f"[i] {case['id']}", flush=True)
        mirror = _clone(case["repo"], args.out / "_mirrors" / case["id"])
        commit = _git("rev-parse", case["fix_commit"], cwd=mirror)
        parent = _git("rev-parse", f"{commit}^", cwd=mirror)

        root = args.out / "cases" / case["id"]
        _worktree(mirror, parent, root / "insecure")
        _worktree(mirror, commit, root / "secure")

        sites = fix_sites(mirror, commit, case["paths"])
        if not sites:
            # A case whose fix touches none of its declared paths proves nothing:
            # every finding is unlocated, so the case can never be detected and
            # can never fail either. It would sit in the corpus looking like
            # coverage. This is how the seed entry was caught - a commit matched
            # by message that only changed a CLI client, not the on-chain program.
            touched = _git("diff", "--name-only", f"{commit}^", commit, cwd=mirror)
            raise SystemExit(
                f"[e] {case['id']}: the fix at {commit[:9]} touches none of "
                f"{case['paths']}.\n    It changed: {touched.splitlines()[:5]}\n"
                f"    Either the paths are wrong or this is not a case."
            )

        expected["cases"].append({
            "id": case["id"],
            "class": case["class"],
            "fix_sites": sites,
        })
        print(f"    {parent[:9]} -> {commit[:9]}  "
              f"{sum(len(v) for v in sites.values())} fix line(s)", flush=True)

    (args.out / "expected.json").write_text(json.dumps(expected, indent=1))
    print(f"\n[i] {len(cases)} case(s) under {args.out / 'cases'}")
    print(f"[i] fix sites written to {args.out / 'expected.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
