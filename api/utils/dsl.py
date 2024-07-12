# WARNING: Unsafe. Use at your own risk.
from typing import Optional
from ast import NodeTransformer, parse, AST
import builtins
import io
import json
import sys
from types import ModuleType

# regular print, but tries to decode printed json outputs (to get a proper json instead of python-flavoured json)
def print_try_jsonify(*args, **kwargs):
    new_args = []
    for arg in args:
        try:
            json_str = json.dumps(arg)
            new_args.append(json_str)
        except (TypeError, ValueError):
            new_args.append(arg)
    print(*new_args, **kwargs)

allowed_builtins = {"print", "len", "range", "dict", "list", "tuple", "set"}
allowed_imports = {}
sandbox_globals = {
    "__builtins__": {"__import__": __import__},
    "print": print_try_jsonify,
    "len": len,
    "range": range,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "set": set,
}


class SandboxTransformer(NodeTransformer):
    def visit(self, node):
        if isinstance(node, (AST, list, tuple)):
            return super().visit(node)
        return node

    def visit_Import(self, node):
        if node.names[0].name not in allowed_imports:
            raise ImportError(f"[e] Import not allowed: {node.names[0].name}")
        return node

    def visit_ImportFrom(self, node):
        if node.module not in allowed_imports:
            raise ImportError(f"[e] Import from not allowed: {node.module}")
        return node

    def visit_Call(self, node):
        func_id = getattr(node.func, "id", None)
        if func_id:
            builtins_dict = (
                vars(builtins) if isinstance(__builtins__, ModuleType) else __builtins__
            )

            if func_id in builtins_dict and func_id not in allowed_builtins:
                raise RuntimeError(f"[e] Use of built-in function is not allowed: {func_id}")

        return self.generic_visit(node)



def wrapped_exec(code: str) -> list:
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        tree = parse(code)
        transformer = SandboxTransformer()
        transformer.visit(tree)
        exec(compile(tree, filename="<ast>", mode="exec"), sandbox_globals)
    finally:
        sys.stdout = old_stdout

    return redirected_output.getvalue().splitlines()


def inject_code_lines(code: str, args: list) -> str:
    arg_lines = "\n".join(args)
    return arg_lines + "\n" + code


def extract_json_output(data: str) -> Optional[dict]:
    node_data = None
    try:
        node_data = json.loads(data)
        if "ident" not in node_data or "src" not in node_data:
            print(f"[w] Dropping output node data without ident: {data}")
            raise ValueError
    except json.JSONDecodeError:
        print(f"[w] Dropping output not json serializeable: {data}")
        return None
    except:
        return None
    return node_data
