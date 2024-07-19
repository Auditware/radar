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
