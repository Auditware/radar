"""Gate: rules that reason across files must be exercised across files.

Almost every rule confines itself to one source - `for source, nodes in ast:`
hands it one file's nodes and the loop body decides from those alone. A few do
not: `missing_two_step_ownership_transfer` walks every source to collect the
project's function names, then walks them again to decide. That second pass is
the whole rule, and nothing tested it, because 250 of the 254 mock variants hold
a single source file. A rule whose cross-file pass silently stopped working
would keep passing its own mock.

Each fixture directory is a small multi-file project, scanned the way a real
scan scans a folder:

    fires/   the project genuinely has the bug          -> must report
    quiet/   the answer is only correct across files    -> must stay silent

`quiet/` is the one that matters. Its two halves are split deliberately: judged
one file at a time the rule reports `transferOwnership` as a one-step handover,
because `acceptOwnership` lives in the other file. It stays silent only if the
first pass really did see the whole project. Merge the two files and the fixture
stops testing anything.
"""

from pathlib import Path

import pytest
import yaml

from utils.ast import generate_program_ast_for_folder
from utils.dsl.dsl import inject_code_lines, process_template_outputs, wrapped_exec

FIXTURES = Path(__file__).resolve().parent / "cross_file_fixtures"
TEMPLATES = Path(__file__).resolve().parent.parent / "builtin_templates"


def _project_ast(directory: Path, language: str):
    """Build the project AST the way `views.py` builds one for a folder."""
    if language == "solidity":
        from utils.solidity_compiler import compile_solidity_files

        return compile_solidity_files(sorted(directory.rglob("*.sol")), base_path=directory)
    return generate_program_ast_for_folder(directory)


def _run(data, directory: Path):
    language = data.get("language", "rust")
    blob = _project_ast(directory, language)
    code = inject_code_lines(
        data["rule"], [f"ast = parse_ast({blob}, language='{language}').items()"]
    )
    return process_template_outputs(wrapped_exec(code), data).get("locations", [])


def _cases():
    found = []
    for stem_dir in sorted(FIXTURES.glob("*")):
        if not stem_dir.is_dir():
            continue
        for expectation in ("fires", "quiet"):
            variant = stem_dir / expectation
            if variant.is_dir():
                found.append((stem_dir.name, expectation, variant))
    return found


CASES = _cases()


@pytest.mark.active_runtime
@pytest.mark.parametrize(
    "stem,expectation,directory", CASES,
    ids=[f"{s}-{e}" for s, e, _ in CASES],
)
def test_rule_decides_across_the_whole_project(stem, expectation, directory):
    template_path = TEMPLATES / f"{stem}.yaml"
    assert template_path.exists(), f"no template {stem}.yaml for {directory.name}"

    sources = sorted(p.name for p in directory.iterdir() if p.suffix in (".rs", ".sol"))
    assert len(sources) > 1, (
        f"{directory} holds {sources}; a cross-file fixture needs more than one "
        "source or it tests nothing this suite does not already cover"
    )

    data = yaml.safe_load(template_path.read_text())
    locations = _run(data, directory)

    if expectation == "fires":
        assert locations, (
            f"{stem} reported nothing on a multi-file project that has the bug "
            f"(sources: {sources})"
        )
    else:
        assert not locations, (
            f"{stem} reported {locations} on a project that is correct once every "
            f"file is considered (sources: {sources}). The answer is in a file the "
            "rule did not take into account."
        )
