"""Telling test code from the code that ships.

Test code is held to a different standard on purpose. A test unwraps, hardcodes
a key, reuses one PDA across two domains and skips the owner check, because
doing any of that the production way would obscure what is being tested or make
the case impossible to set up. Reporting those as vulnerabilities is not a
finding, it is a fixed cost every user pays on every scan, and it trains people
to skim the report - which is how the real finding gets missed.

So tests are excluded by default and `--include-tests` puts them back.

Two filters, because Rust puts tests in two places:

  - integration tests and fixtures live in files, under a `tests/` directory or
    in a file named for testing;
  - unit tests live *inside* the module they test, as `#[cfg(test)] mod tests`,
    which is the dominant convention and which no path filter can see.

Deliberately not excluded: `benches/` and `examples/`. A benchmark is not
asserting correctness and an example is code users are invited to copy, so
neither has the "written unsafely on purpose" property that justifies skipping
tests.
"""

from pathlib import Path

# Directory names that mean "this tree is tests".
TEST_DIRECTORIES = ("tests", "test", "testing", "__tests__")

# Whole file names, and prefix/suffix conventions, that mean "this file is tests".
TEST_FILE_NAMES = ("tests.rs", "test.rs")
TEST_FILE_PREFIXES = ("test_",)
TEST_FILE_SUFFIXES = ("_test.rs", "_tests.rs", ".test.rs")

# The last path segment of an attribute that marks an item as a test. Matching
# the last segment rather than the whole path is what makes `#[tokio::test]`,
# `#[actix_rt::test]` and a bare `#[test]` one rule instead of a list.
TEST_ATTRIBUTE_TAILS = ("test", "bench")


def is_test_path(path, relative_to=None) -> bool:
    """True when a source file's location marks it as test code.

    `relative_to` is the root being scanned, and directory names are only
    considered below it. Without that, someone whose checkout happens to live
    in `~/work/tests/my-program` has every file classified as test code and
    gets an empty scan with nothing to explain it - the silent-clean failure
    this whole feature must not introduce.
    """
    path = Path(path)

    directory = path.parent
    if relative_to is not None:
        try:
            directory = directory.relative_to(Path(relative_to))
        except ValueError:
            # Not under the root; fall back to judging the whole path.
            pass

    for part in directory.parts:
        if part.lower() in TEST_DIRECTORIES:
            return True

    name = path.name.lower()
    if name in TEST_FILE_NAMES:
        return True
    for prefix in TEST_FILE_PREFIXES:
        if name.startswith(prefix):
            return True
    for suffix in TEST_FILE_SUFFIXES:
        if name.endswith(suffix):
            return True
    return False


def _tokens_name_test(tokens) -> bool:
    """Whether a `cfg(...)` token tree mentions `test` at any depth.

    `#[cfg(test)]` is the common case, but `#[cfg(any(test, feature = "x"))]`
    nests it, and a flat scan of the top level would miss that.
    """
    if isinstance(tokens, dict):
        if tokens.get("ident") == "test":
            return True
        return any(_tokens_name_test(value) for value in tokens.values())
    if isinstance(tokens, list):
        return any(_tokens_name_test(item) for item in tokens)
    return False


def _path_tail(meta_path) -> str:
    segments = (meta_path or {}).get("segments") or []
    if not segments:
        return ""
    return segments[-1].get("ident") or ""


def is_test_attribute(attr) -> bool:
    """Whether one attribute marks the item it sits on as test-only."""
    if not isinstance(attr, dict):
        return False
    meta = attr.get("meta") or {}

    # `#[test]`, `#[bench]`, `#[tokio::test]`
    if _path_tail(meta.get("path")) in TEST_ATTRIBUTE_TAILS:
        return True

    # `#[cfg(test)]`, `#[cfg(any(test, ...))]`
    listed = meta.get("list")
    if isinstance(listed, dict) and _path_tail(listed.get("path")) == "cfg":
        return _tokens_name_test(listed.get("tokens"))

    return False


def is_test_item(item) -> bool:
    """Whether a top-level or nested AST item is test-only."""
    if not isinstance(item, dict):
        return False
    for body in item.values():
        if not isinstance(body, dict):
            continue
        for attr in body.get("attrs") or []:
            if is_test_attribute(attr):
                return True
    return False


def strip_test_items(items):
    """Drop test-only items, at any nesting depth.

    Recurses because `#[cfg(test)] mod tests` is usually inside the module it
    tests, and that module may itself be nested. Returns a new list; the input
    is not modified.
    """
    if not isinstance(items, list):
        return items

    kept = []
    for item in items:
        if is_test_item(item):
            continue
        if isinstance(item, dict):
            pruned = {}
            for key, body in item.items():
                if isinstance(body, dict) and isinstance(body.get("items"), list):
                    body = dict(body)
                    body["items"] = strip_test_items(body["items"])
                pruned[key] = body
            item = pruned
        kept.append(item)
    return kept
