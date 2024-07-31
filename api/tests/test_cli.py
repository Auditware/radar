import subprocess
import pytest
from pathlib import Path

pytestmark = [pytest.mark.active_runtime]

CLI_PATH = Path("../radar")
CONTRACT_PATH = Path("tests/mocks/anchor-test")
OUTPUT_PATH = Path("tests/mocks/output.json")
SOURCE_PATH = "programs/anchor-test"
TEMPLATES_PATH = Path("builtin_templates")


@pytest.fixture
def cleanup():
    yield
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()


def run_cli_command(args):
    result = subprocess.run([CLI_PATH] + args, capture_output=True, text=True)
    return result


def test_no_args(cleanup):
    result = run_cli_command([])
    assert result.returncode != 0
    assert "Usage" in result.stdout


def test_only_path_arg(cleanup):
    result = run_cli_command(["-p", str(CONTRACT_PATH)])
    assert result.returncode == 0


def test_with_ast_and_output(cleanup):
    result = run_cli_command(["-p", str(CONTRACT_PATH), "-a", "-o", str(OUTPUT_PATH)])
    assert result.returncode == 0
    assert OUTPUT_PATH.exists()


def test_with_source(cleanup):
    result = run_cli_command(["-p", str(CONTRACT_PATH), "-s", str(SOURCE_PATH)])
    assert result.returncode == 0


def test_with_source_and_traversed_path(cleanup):
    result = run_cli_command(
        ["-p", "../api/tests/mocks/anchor-test", "-s", str(SOURCE_PATH)]
    )
    assert result.returncode == 0


def test_with_templates(cleanup):
    result = run_cli_command(["-p", str(CONTRACT_PATH), "-t", str(TEMPLATES_PATH)])
    assert result.returncode == 0
