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


# --- Handler narrowing -------------------------------------------------------
#
# Every template guards its loop body with `except: continue`, because that was
# the only way to catch what `exit_on_none` / `exit_on_value` raise. That same
# handler used to catch the rule's own bugs, so a broken rule reported zero
# findings and the scan came back clean. `SandboxTransformer` now rewrites bare
# handlers to `except RuleSkip:`; these pin both halves of that behaviour.

RULE_SKIP_IS_STILL_CAUGHT = """
for i in [1, 2, 3]:
    try:
        raise RuleSkip("not interesting")
    except:
        continue
print('reached-end')
"""

# Real bugs hit while writing rules: a builtin the sandbox does not expose, and
# an unhashable value in a set. Each used to skip every item silently.
#
# The forbidden-builtin case was originally `str()`, which the sandbox has since
# been widened to allow; `getattr` stands in for it because reaching the
# interpreter rather than the values is what stays forbidden. The bug it stands
# for is unchanged: a name the sandbox refuses raises at rule runtime, and that
# error has to reach the caller instead of skipping the item.
RULE_BUGS_THAT_MUST_PROPAGATE = [
    "for i in [1]:\n    try:\n        x = getattr(i, 'real')\n    except:\n        continue\n",
    "for i in [1]:\n    try:\n        s = set([dict()])\n    except:\n        continue\n",
    "for i in [1]:\n    try:\n        y = 1 + 'a'\n    except:\n        continue\n",
    "for i in [1]:\n    try:\n        y = undefined_name\n    except:\n        continue\n",
]

# A handler that names a type is the author's decision and must be left alone.
EXPLICIT_HANDLER_NOT_WIDENED = """
for i in [1]:
    try:
        y = 1 + 'a'
    except RuleSkip:
        continue
"""


def test_bare_handler_still_catches_the_control_flow_signal():
    assert '"reached-end"' in wrapped_exec(RULE_SKIP_IS_STILL_CAUGHT)


@pytest.mark.parametrize("code", RULE_BUGS_THAT_MUST_PROPAGATE)
def test_bare_handler_no_longer_swallows_rule_bugs(code):
    with pytest.raises(Exception):
        wrapped_exec(code)


def test_explicit_handler_is_not_widened():
    with pytest.raises(TypeError):
        wrapped_exec(EXPLICIT_HANDLER_NOT_WIDENED)


def test_exit_helpers_raise_the_skip_signal():
    """`exit_on_none` / `exit_on_value` are control flow, not errors.

    They must not raise `StopIteration`: inside a generator that becomes a
    `RuntimeError` (PEP 479), and it is indistinguishable from an exhausted
    iterator anywhere else.
    """
    from utils.dsl.dsl_ast_iterator import ASTNodeList, ASTNodeListGroup, RuleSkip

    assert not issubclass(RuleSkip, StopIteration)

    with pytest.raises(RuleSkip):
        ASTNodeList([]).exit_on_none()
    with pytest.raises(RuleSkip):
        ASTNodeList([object()]).exit_on_value()
    with pytest.raises(RuleSkip):
        ASTNodeListGroup([]).exit_on_none()
    with pytest.raises(RuleSkip):
        ASTNodeList([]).first()
