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


##########################
## DSL helper functions ##
def get_all_derives(ast: dict, derived_name: str) -> list:
    derives = []

    def extract_derive_calls(node):
        if isinstance(node, dict):
            if "meta" in node and "list" in node["meta"]:
                path_segments = node["meta"]["list"]["path"]["segments"]
                if path_segments and path_segments[-1]["ident"] == "derive":
                    tokens = node["meta"]["list"]["tokens"]
                    if tokens and tokens[0]["ident"] == derived_name:
                        derives.append(node)
            for key, value in node.items():
                extract_derive_calls(value)
        elif isinstance(node, list):
            for item in node:
                extract_derive_calls(item)

    extract_derive_calls(ast)
    return derives


def find_specific_member_access(ast: dict, member_name: str) -> list:
    results = []

    def search_nodes(nodes):
        for i in range(len(nodes) - 1):
            if isinstance(nodes[i], dict) and isinstance(nodes[i + 1], dict):
                if (
                    nodes[i].get("punct", {}).get("op") == "."
                    and nodes[i + 1].get("ident") == member_name
                ):
                    results.append((nodes[i + 1]))

    def traverse_ast(node):
        if isinstance(node, list):
            search_nodes(node)
            for sub_node in node:
                traverse_ast(sub_node)
        elif isinstance(node, dict):
            for value in node.values():
                traverse_ast(value)

    traverse_ast(ast)
    return results


def get_first_node(ast: dict) -> dict:
    if isinstance(ast, list):
        first_node = ast[0]
    elif isinstance(ast, dict):
        first_node = next(iter(ast.values()))
        if isinstance(first_node, list):
            first_node = first_node[0]

    while isinstance(first_node, dict):
        keys = list(first_node.keys())
        if "src" in keys and "ident" in keys:
            return first_node
        first_node = first_node[keys[0]]
        if isinstance(first_node, list):
            first_node = first_node[0]
    return first_node


def find_compare_operations(ast: dict, ident_name: str) -> dict:
    def search_node(node):
        results = []
        if isinstance(node, dict):
            if node.get("ident") == ident_name:
                results.append(node)

            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    if key == "expr":
                        results.extend(search_node(value))
                    else:
                        results.extend(search_node(value))

        elif isinstance(node, list):
            for item in node:
                results.extend(search_node(item))
        return results

    def search_expr(expr):
        results = []
        if isinstance(expr, dict):
            if "expr" in expr:
                results.extend(search_node(expr["expr"]))
            else:
                for value in expr.values():
                    if isinstance(value, (dict, list)):
                        results.extend(search_expr(value))
        elif isinstance(expr, list):
            for item in expr:
                results.extend(search_expr(item))
        return results

    return search_expr(ast)


def find_compare_operations_between(ast: dict, ident1: str, ident2: str) -> list:
    comparisons = []

    def traverse(node):
        if isinstance(node, dict):
            if "binary" in node:
                left = node["binary"]["left"]
                right = node["binary"]["right"]
                if (check_ident(left, ident1) and check_ident(right, ident2)) or (
                    check_ident(left, ident2) and check_ident(right, ident1)
                ):
                    comparisons.append(node)
            for key in node:
                traverse(node[key])
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    def check_ident(node, ident):
        if isinstance(node, dict):
            if "ident" in node and node["ident"] == ident:
                return True
            for key in node:
                if check_ident(node[key], ident):
                    return True
        elif isinstance(node, list):
            for item in node:
                if check_ident(item, ident):
                    return True
        return False

    traverse(ast)
    return comparisons


def find_single_node_by_name(ast: dict, ident_name: str) -> dict:
    def search_nodes(node):
        if isinstance(node, dict):
            if "ident" in node and node["ident"] == ident_name:
                return node
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    result = search_nodes(value)
                    if result:
                        return result
        elif isinstance(node, list):
            for item in node:
                result = search_nodes(item)
                if result:
                    return result
        return None

    return search_nodes(ast)

def find_mutables(ast: dict) -> dict:
    def search_mutable(node):
        results = []
        if isinstance(node, dict):
            if node.get("mut") == True:
                ident_node = find_ident_node(node)
                if ident_node:
                    results.append(ident_node)
            for k, v in node.items():
                results.extend(search_mutable(v))
        elif isinstance(node, list):
            for item in node:
                results.extend(search_mutable(item))
        return results

    def find_ident_node(node):
        if isinstance(node, dict):
            if "ident" in node:
                return node
            for k, v in node.items():
                result = find_ident_node(v)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = find_ident_node(item)
                if result:
                    return result
        return None

    results = search_mutable(ast)
    unique_results = []
    seen = set()
    for result in results:
        ident = result["ident"]
        if ident not in seen:
            unique_results.append(result)
            seen.add(ident)
    return unique_results

def find_account_typed_nodes(ast: dict, ident_name: str) -> list:
    def recurse(node):
        results = []
        if isinstance(node, dict):
            if node.get("ident") == ident_name:
                if "ty" in node:
                    ty_path = node["ty"].get("path")
                    if ty_path:
                        for segment in ty_path.get("segments", []):
                            if segment.get("ident") == "Account":
                                results.append(node)
            for key, value in node.items():
                results.extend(recurse(value))
        elif isinstance(node, list):
            for item in node:
                results.extend(recurse(item))
        return results

    return recurse(ast)

def find_node_with_method_call(ast, ident, method):
    def search_node(node):
        if isinstance(node, dict):
            if "method_call" in node:
                method_call = node["method_call"]
                if method_call["method"] == method:
                    receiver = method_call["receiver"]
                    if find_ident_in_receiver(receiver, ident):
                        return get_receiver_data(receiver)
            for key, value in node.items():
                result = search_node(value)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = search_node(item)
                if result:
                    return result
        return None

    def find_ident_in_receiver(receiver, ident):
        if isinstance(receiver, dict):
            if "ident" in receiver and receiver["ident"] == ident:
                return True
            for key, value in receiver.items():
                if find_ident_in_receiver(value, ident):
                    return True
        elif isinstance(receiver, list):
            for item in receiver:
                if find_ident_in_receiver(item, ident):
                    return True
        return False

    def get_receiver_data(receiver):
        if isinstance(receiver, dict) and "field" in receiver:
            return receiver["field"]
        return receiver

    return search_node(ast)
##########################

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
    "get_all_derives": get_all_derives,
    "get_first_node": get_first_node,
    "find_account_typed_nodes": find_account_typed_nodes,
    "find_compare_operations": find_compare_operations,
    "find_compare_operations_between": find_compare_operations_between,
    "find_mutables": find_mutables,
    "find_node_with_method_call": find_node_with_method_call,
    "find_single_node_by_name": find_single_node_by_name,
    "find_specific_member_access": find_specific_member_access,
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
