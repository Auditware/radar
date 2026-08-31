"""Inline finding suppression via source comments.

Teams adopting a scanner on an existing codebase need a way to accept a specific
line without turning off a whole rule. radar honours two comment markers:

    // radar-disable-line [RuleId ...]           on the finding's own line
    // radar-disable-next-line [RuleId ...]       on the line directly above

With no rule id the marker suppresses every finding on the target line; with one
or more ids (space/comma separated) it suppresses only those rules. A rule id is
matched loosely against the finding name so both the SARIF id form
(`Missing_Signer_Check`) and a lowercase-hyphen form (`missing-signer-check`)
work, case-insensitively.

Both Rust (`//`) and Solidity (`//`) line comments use the same marker; this runs
in the API service where the scanned sources are on disk.
"""

import re
from pathlib import Path

_MARKER_RE = re.compile(
    r"//\s*radar-disable-(?P<kind>next-line|line)\b(?P<rules>[^\n]*)"
)


def _rule_tokens(name: str) -> set:
    """Loose match keys for a finding name."""
    lowered = name.strip().lower()
    return {
        name.strip(),
        name.replace(" ", "_"),
        lowered,
        lowered.replace(" ", "_"),
        lowered.replace(" ", "-"),
    }


def _read_lines(file_path: str):
    # Deliberately uncached: workers are long-lived and the same container path
    # holds different sources across scans, so caching by path would leak one
    # scan's file content into the next.
    try:
        return Path(file_path).read_text(errors="replace").splitlines()
    except OSError:
        return None


def _marker_on_line(lines, line_no: int):
    """Return (present, rule_ids set or None) for a marker on 1-based line_no."""
    if line_no < 1 or line_no > len(lines):
        return (False, None)
    match = _MARKER_RE.search(lines[line_no - 1])
    if not match:
        return (False, None)
    raw = match.group("rules").strip()
    if not raw:
        return (True, None)  # bare marker: all rules
    ids = {tok for tok in re.split(r"[\s,]+", raw) if tok}
    return (True, ids)


def is_suppressed(file_path: str, line_no: int, rule_name: str, lines=None) -> bool:
    if lines is None:
        lines = _read_lines(file_path)
    if lines is None:
        return False

    keys = _rule_tokens(rule_name)
    keys_lower = {k.lower() for k in keys}

    # A `disable-line` marker on the finding line, or a `disable-next-line`
    # marker on the line above, both target this line.
    same = _marker_on_line(lines, line_no)
    above = _marker_on_line(lines, line_no - 1)

    for present, rule_ids in (same, above):
        if not present:
            continue
        if rule_ids is None:
            return True
        if {r.lower() for r in rule_ids} & keys_lower:
            return True
    return False


def _location_file_and_line(location: str):
    """Parse `file:line:colrange` (file may itself contain colons on Windows,
    but scan paths here are POSIX). Returns (file, line) or None."""
    parts = location.rsplit(":", 2)
    if len(parts) < 2:
        return None
    file_path = parts[0]
    try:
        line_no = int(parts[1])
    except ValueError:
        return None
    return (file_path, line_no)


def filter_suppressed_locations(locations, rule_name: str):
    """Drop locations carrying an inline suppression marker for rule_name.

    Each source file is read at most once per call (not cached across calls, so
    a long-lived worker never serves a prior scan's file content).
    """
    file_cache = {}
    kept = []
    for location in locations:
        parsed = _location_file_and_line(location)
        if parsed is None:
            kept.append(location)
            continue
        file_path, line_no = parsed
        if file_path not in file_cache:
            file_cache[file_path] = _read_lines(file_path)
        if not is_suppressed(file_path, line_no, rule_name, file_cache[file_path]):
            kept.append(location)
    return kept
