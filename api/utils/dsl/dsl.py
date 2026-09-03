# WARNING: Unsafe. Use at your own risk.
import inspect
from typing import Optional
from ast import Load, Name, NodeTransformer, parse, AST, fix_missing_locations
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
    # Referenced by the handlers `SandboxTransformer` rewrites, so it has to
    # resolve at rule runtime even though no template names it directly.
    "RuleSkip": dsl_ast_iterator.RuleSkip,
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

    def visit_ExceptHandler(self, node):
        """Narrow a catch-everything handler to the DSL's control-flow signal.

        Every rule guards its loop body with `except: continue`, because that is
        the only way to catch what `exit_on_none` / `exit_on_value` raise. The
        cost was that the same handler caught the rule's own bugs: a template
        that referenced a forbidden builtin, or put an unhashable value in a
        set, skipped every item and reported nothing - which is indistinguishable
        from a scan that found nothing wrong. Three rules shipped that way.

        `run_scan_task` already does the right thing with a template that
        raises: it records the error and the controller exits non-zero. This
        just stops the rule from eating the error first.

        Only bare handlers are rewritten, so a deliberate catch is never
        silently narrowed. In practice `RuleSkip` is the only type a rule can
        name - the sandbox exposes no builtin exception classes, which is why
        `except:` was the sole option available to template authors to begin
        with, and why this had to be fixed here rather than in 124 templates.
        """
        if node.type is None:
            node.type = Name(id="RuleSkip", ctx=Load())
        return self.generic_visit(node)

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
        # The rewritten `except` handlers are synthesised nodes with no
        # position, and compile() requires one on every node.
        fix_missing_locations(tree)
        # Execute into a fresh copy of the base globals. Celery prefork workers
        # are long-lived and run many templates per process; a shared globals
        # dict lets one template's top-level names (ast, nodes, loop vars, …)
        # leak into the next, making a scan's results depend on execution order
        # and which worker ran it. A per-exec copy keeps each template isolated.
        exec_globals = dict(sandbox_globals)
        exec(compile(tree, filename="<ast>", mode="exec"), exec_globals)
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

    def extract_location(node):
        """Extract location string from either Rust or Solidity node format."""
        # Rust format: src is a dict with file, line, start_col, end_col
        if "src" in node and isinstance(node["src"], dict):
            src = node["src"]
            if src is not None:
                return f"{src['file']}:{src['line']}:{src['start_col']}-{src['end_col']}"
        
        # Solidity format: src_calculated has the location, file separate
        if "src_calculated" in node and node["src_calculated"]:
            return node["src_calculated"]
        
        # Fallback: construct from file + src string (Solidity raw format)
        if "file" in node and "src" in node and isinstance(node["src"], str):
            # src format is "start:length:fileIndex", we use file+src as is
            return f"{node['file']}:{node['src']}"
            
        return None

    for output in template_outputs:
        valid_output = extract_json_output(output)
        if valid_output is not None:
            # Handle single node case
            if isinstance(valid_output, dict):
                # print("[i] Finding-valid printed output detected")
                location = extract_location(valid_output)
                if location:
                    finding_data["locations"].append(location)
            
            # Handle list of nodes case
            elif isinstance(valid_output, list):
                # print(f"[i] Finding-valid printed output list detected with {len(valid_output)} nodes")
                for node in valid_output:
                    location = extract_location(node)
                    if location:
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
            # Support both Rust (ident+src) and Solidity (node_type+src_calculated) formats
            is_rust_node = "ident" in node_data and "src" in node_data
            is_solidity_node = "node_type" in node_data and ("src" in node_data or "src_calculated" in node_data)
            
            if not (is_rust_node or is_solidity_node):
                # print(f"[w] Dropping output node data without required fields: {data}")
                raise ValueError
        
        # Handle list of nodes case
        elif isinstance(node_data, list):
            for node in node_data:
                if not isinstance(node, dict):
                    # print(f"[w] Dropping output list containing non-dict: {data}")
                    raise ValueError
                    
                is_rust_node = "ident" in node and "src" in node
                is_solidity_node = "node_type" in node and ("src" in node or "src_calculated" in node)
                
                if not (is_rust_node or is_solidity_node):
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
