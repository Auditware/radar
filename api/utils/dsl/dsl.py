# WARNING: Unsafe. Use at your own risk.
import inspect
from typing import Optional
from ast import NodeTransformer, parse, AST
import builtins
import io
import json
import sys
from types import ModuleType
from utils.dsl import dsl_ast_iterator


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


allowed_builtins = {"print", "len", "range", "dict", "list", "tuple", "set", "type"}
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
    "type": type,
}
sandbox_globals.update(
    {
        name: func
        for name, func in inspect.getmembers(
            dsl_ast_iterator,
            predicate=lambda f: inspect.isfunction(f)
            and f.__module__ == dsl_ast_iterator.__name__,
        )
    }
)


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
                raise RuntimeError(
                    f"[e] Use of built-in function is not allowed: {func_id}"
                )

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


# Iterate over outputs, treat only ast nodes (dict types with an 'ident' & 'src' key on the top level)
def process_template_outputs(template_outputs, yaml_data):
    finding_data = {
        "name": yaml_data["name"],
        "description": yaml_data["description"],
        "severity": yaml_data["severity"],
        "certainty": yaml_data["certainty"],
        "locations": [],
        "debug": [],
    }

    for output in template_outputs:
        valid_output = extract_json_output(output)
        if valid_output is not None:
            # Handle single node case
            if isinstance(valid_output, dict):
                # print("[i] Finding-valid printed output detected")
                src = valid_output["src"]
                location = (
                    f"{src['file']}:{src['line']}:{src['start_col']}-{src['end_col']}"
                )
                finding_data["locations"].append(location)
            
            # Handle list of nodes case
            elif isinstance(valid_output, list):
                # print(f"[i] Finding-valid printed output list detected with {len(valid_output)} nodes")
                for node in valid_output:
                    src = node["src"]
                    location = (
                        f"{src['file']}:{src['line']}:{src['start_col']}-{src['end_col']}"
                    )
                    finding_data["locations"].append(location)
        else:
            finding_data["debug"].append(output)

    if not finding_data["debug"]:
        del finding_data["debug"]

    return finding_data


def extract_json_output(data: str) -> Optional[dict | list]:
    node_data = None
    try:
        node_data = json.loads(data)
        
        # Handle single node case
        if isinstance(node_data, dict):
            if "ident" not in node_data or "src" not in node_data:
                # print(f"[w] Dropping output node data without ident/src: {data}")
                raise ValueError
        
        # Handle list of nodes case
        elif isinstance(node_data, list):
            for node in node_data:
                if not isinstance(node, dict) or "ident" not in node or "src" not in node:
                    # print(f"[w] Dropping output list containing invalid node data: {data}")
                    raise ValueError
        
        else:
            # print(f"[w] Dropping output that is neither dict nor list: {data}")
            raise ValueError
            
    except json.JSONDecodeError:
        # print(f"[w] Dropping output not json serializeable: {data}")
        return None
    except:
        return None
    return node_data
