import pytest
from utils.dsl.dsl import wrapped_exec

malicious_payloads = [
    "() .__class__.__bases__[0].__subclasses__()[40](r'/etc/hosts').read()",
    'importlib.import_module("os").system("ls")',
    '__import__("os").system("id"); x',
    'imp.sys.modules["os"].system("ps")',
    '__builtins__.__dict__["__import__"]("os").system("ls -la")',
    'open("/etc/hosts").read()',
    '"),__import__("os").system("whoami"); x',
    'importlib.__import__("os").system("uname")',
    "getattr(getattr(globals()['__builtins__'], '__im'+'por'+'t__')('o'+'s'), 'sys'+'tem')('cat /etc/hosts')",
    "eval(compile('xx = 1; zz = 3', '<stdin>', 'exec'))",
]

benign_payloads = [
    "print('hello world')",
    "[print(i) for i in range(3)]",
    "for i in range(3): print(i)",
]


@pytest.mark.parametrize("code", malicious_payloads)
def test_wrapped_exec_malicious_payloads_failiure(code):
    with pytest.raises(Exception):
        wrapped_exec(code)


@pytest.mark.parametrize("code", benign_payloads)
def test_wrapped_exec_benign_payloads(code):
    assert (
        wrapped_exec(code) is not None
    ), "Check that benign code executes without errors"


# A rule that dies must not read as a rule that found nothing.
#
# Every template guards its loop with `except: continue`, which is the only way
# to catch what `exit_on_none`/`exit_on_value` raise. While those raised the
# builtin StopIteration, that handler swallowed the template's own bugs too, and
# the rule skipped every item and reported zero findings with no error anywhere.
# Three rules shipped broken that way. `SandboxTransformer` now rewrites bare
# handlers to catch only `RuleSkip`, so real failures reach `run_scan_task`,
# which records them and makes the controller exit non-zero.

CONTROL_FLOW_RULE = """
ast = parse_ast([], language='rust').items()
for source, nodes in ast:
    try:
        nodes.find_by_names("absent").exit_on_none()
        print("unreachable")
    except:
        continue
print("survived")
"""

FORBIDDEN_BUILTIN_RULE = """
ast = parse_ast([], language='rust').items()
try:
    print(str(1))
except:
    pass
"""

RUNTIME_ERROR_RULE = """
ast = parse_ast([], language='rust').items()
try:
    seen = set()
    seen.add(dict())
    print("unreachable")
except:
    pass
"""

NAMED_HANDLER_RULE = """
ast = parse_ast([], language='rust').items()
for source, nodes in ast:
    try:
        nodes.find_by_names("absent").exit_on_none()
    except RuleSkip:
        print("caught deliberately")
print("done")
"""


def test_bare_except_still_swallows_dsl_control_flow():
    """exit_on_* must keep skipping items, or every rule stops working."""
    assert '"survived"' in wrapped_exec(CONTROL_FLOW_RULE)


def test_bare_except_no_longer_hides_a_forbidden_builtin():
    with pytest.raises(RuntimeError, match="built-in function is not allowed"):
        wrapped_exec(FORBIDDEN_BUILTIN_RULE)


def test_bare_except_no_longer_hides_a_runtime_error():
    """The `to_result()`-into-a-set bug, which shipped as a silently dead rule."""
    with pytest.raises(TypeError, match="unhashable"):
        wrapped_exec(RUNTIME_ERROR_RULE)


def test_named_except_handler_is_left_alone():
    """Only bare handlers are rewritten; a handler that names its type is kept.

    `RuleSkip` is the one exception a template can name: the sandbox exposes no
    builtin exception classes, which is why a bare `except:` was the only
    handler a rule could write in the first place.
    """
    assert '"done"' in wrapped_exec(NAMED_HANDLER_RULE)
