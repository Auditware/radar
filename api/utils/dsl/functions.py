def get_first_node(ast: dict) -> dict | None:
    def recursive_search(node):
        if isinstance(node, dict):
            if "ident" in node and "src" in node:
                return node
            for key, value in node.items():
                result = recursive_search(value)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = recursive_search(item)
                if result:
                    return result
        return None

    return recursive_search(ast)


def get_node_with_method_call(ast: dict, ident: str, method: str) -> dict | None:
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


def get_node_by_name(ast: dict, ident_name: str) -> dict:
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


def find_derives(ast: dict, derived_name: str) -> list:
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


def find_specific_member_accesses(ast: dict, member_name: str) -> list:
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


def find_mutables(ast: dict) -> list:
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
    return list(unique_results)


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


def find_cpi_nodes(ast: dict) -> tuple[list, list]:
    def find_invokes(node):
        invoke_nodes = []
        cpi_nodes = []
        if isinstance(node, dict):
            if node.get("func") and "path" in node["func"]:
                path_segments = node["func"]["path"].get("segments", [])
                if len(path_segments) > 2:
                    if (
                        path_segments[-3].get("ident") == "solana_program"
                        and path_segments[-2].get("ident") == "program"
                        and path_segments[-1].get("ident") == "invoke"
                    ):
                        invoke_nodes.append(path_segments[-1])
                        cpi_nodes.extend(find_args_with_ident(node.get("args", [])))
            for key, value in node.items():
                inv, cpi = find_invokes(value)
                invoke_nodes.extend(inv)
                cpi_nodes.extend(cpi)
        elif isinstance(node, list):
            for item in node:
                inv, cpi = find_invokes(item)
                invoke_nodes.extend(inv)
                cpi_nodes.extend(cpi)
        return invoke_nodes, cpi_nodes

    def find_args_with_ident(args):
        result = []
        for arg in args:
            if isinstance(arg, dict):
                if "ident" in arg:
                    result.append(arg)
                else:
                    for key, value in arg.items():
                        if isinstance(value, (dict, list)):
                            result.extend(find_args_with_ident([value]))
            elif isinstance(arg, list):
                result.extend(find_args_with_ident(arg))
        return result

    return find_invokes(ast)


def find_cpi_nodes_by_order(cpi_nodes: list, idents: list) -> list:
    def match_idents(nodes, idents):
        if not idents:
            return []

        current_ident = idents[0]
        remaining_idents = idents[1:]

        for node in nodes:
            if isinstance(node, dict) and "ident" in node:
                if node["ident"] == current_ident:
                    if not remaining_idents:
                        return [node]
                    result = match_idents(nodes, remaining_idents)
                    if result:
                        return [node] + result
            elif isinstance(node, list):
                result = match_idents(node, idents)
                if result:
                    return result

        return []

    result = match_idents(cpi_nodes, idents)
    return result


def find_method_calls(ast: dict, caller_ident: str, method_name: str) -> list:
    def extract_ast_with_ident(node):
        if isinstance(node, dict):
            if "ident" in node:
                return node
            for key, value in node.items():
                result = extract_ast_with_ident(value)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = extract_ast_with_ident(item)
                if result:
                    return result
        return None

    def find_calls(node):
        if isinstance(node, dict):
            if "method_call" in node and node["method_call"]["method"] == method_name:
                receiver = node["method_call"]["receiver"]
                receiver_ast = extract_ast_with_ident(receiver)
                caller = extract_ast_with_ident(node)
                if receiver_ast and caller and caller.get("ident") == caller_ident:
                    results.append(receiver_ast)
            for key, value in node.items():
                find_calls(value)
        elif isinstance(node, list):
            for item in node:
                find_calls(item)

    results = []
    find_calls(ast)
    return results


def find_assignments_between(ast: dict, method_call: str, value: str) -> list:
    idents = []

    def traverse(node):
        if isinstance(node, dict):
            if "assign" in node:
                left = node["assign"]["left"]
                right = node["assign"]["right"]
                if check_method_call(left, method_call) and check_value(right, value):
                    ident = find_first_ident(left)
                    if ident:
                        idents.append(ident)
            for key in node:
                traverse(node[key])
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    def check_method_call(node, method_call):
        if isinstance(node, dict):
            if "method_call" in node and node["method_call"]["method"] == method_call:
                return True
            for key in node:
                if check_method_call(node[key], method_call):
                    return True
        elif isinstance(node, list):
            for item in node:
                if check_method_call(item, method_call):
                    return True
        return False

    def check_value(node, value):
        if isinstance(node, dict):
            if "lit" in node and "int" in node["lit"] and node["lit"]["int"] == value:
                return True
            for key in node:
                if check_value(node[key], value):
                    return True
        elif isinstance(node, list):
            for item in node:
                if check_value(item, value):
                    return True
        return False

    def find_first_ident(node):
        if isinstance(node, dict):
            if "ident" in node:
                return node
            for key in node:
                result = find_first_ident(node[key])
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = find_first_ident(item)
                if result:
                    return result
        return None

    traverse(ast)
    return idents


def find_functions_by_names(ast: dict, function_names: list) -> list:
    def find_function(node, names):
        if isinstance(node, dict):
            if "fn" in node and node["fn"]["ident"] in names:
                return [node["fn"]]
            results = []
            for key, value in node.items():
                results.extend(find_function(value, names))
            return results
        elif isinstance(node, list):
            results = []
            for item in node:
                results.extend(find_function(item, names))
            return results
        return []

    return find_function(ast, function_names)


def find_nodes_by_names(ast: dict, ident_names: list) -> list:
    def search_nodes(node, names):
        results = []
        if isinstance(node, dict):
            if "ident" in node and node["ident"] in names:
                results.append(node)
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    results.extend(search_nodes(value, names))
        elif isinstance(node, list):
            for item in node:
                results.extend(search_nodes(item, names))
        return results

    return search_nodes(ast, ident_names)


def find_member_access_chain(ast: dict, member_names: list) -> list:
    results = []

    def search_nodes(nodes):
        n = len(nodes)
        m = len(member_names)
        i = 0

        while i <= n - m * 2 + 1:
            matched = True
            temp_result = []
            current_index = i
            for j in range(m):
                while (
                    current_index < n
                    and nodes[current_index].get("ident") != member_names[j]
                ):
                    current_index += 1

                if (
                    current_index >= n
                    or nodes[current_index].get("ident") != member_names[j]
                ):
                    matched = False
                    break

                temp_result.append(nodes[current_index])

                if j < m - 1:
                    current_index += 1
                    while current_index < n and nodes[current_index].get(
                        "punct", {}
                    ).get("op") not in [".", ":"]:
                        current_index += 1

                    if current_index >= n:
                        matched = False
                        break

                current_index += 1

            if matched:
                results.extend(temp_result)
                i = current_index
            else:
                i += 1

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


def find_segmented_nodes_by_order(ast: dict, idents: list) -> list:
    def search_segments(nodes, idents):
        if not idents:
            return []

        current_ident = idents[0]
        remaining_idents = idents[1:]

        for i, node in enumerate(nodes):
            if isinstance(node, dict) and "ident" in node:
                if node["ident"] == current_ident:
                    if not remaining_idents:
                        return [node]
                    nested_nodes = nodes[
                        i + 1 :
                    ]  # Continue searching from the next node in the same list
                    result = search_segments(nested_nodes, remaining_idents)
                    if result:
                        return [node] + result
        return []

    def find_segments_key(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "segments" and isinstance(value, list):
                    result = search_segments(value, idents)
                    if result:
                        return result
                elif isinstance(value, (dict, list)):
                    result = find_segments_key(value)
                    if result:
                        return result
        elif isinstance(node, list):
            for item in node:
                result = find_segments_key(item)
                if result:
                    return result
        return []

    return find_segments_key(ast)


def find_segmented_nodes_by_order(ast_nodes: list, idents: list) -> list:
    def search_segments(nodes, idents):
        if not idents:
            return []

        current_ident = idents[0]
        remaining_idents = idents[1:]

        for i, node in enumerate(nodes):
            if isinstance(node, dict) and "ident" in node:
                if node["ident"] == current_ident:
                    if not remaining_idents:
                        return [node]
                    nested_nodes = nodes[
                        i + 1 :
                    ]  # Continue searching from the next node in the same list
                    result = search_segments(nested_nodes, remaining_idents)
                    if result:
                        return [node] + result
        return []

    def find_segments_key(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "segments" and isinstance(value, list):
                    result = search_segments(value, idents)
                    if result:
                        return result
                elif isinstance(value, (dict, list)):
                    result = find_segments_key(value)
                    if result:
                        return result
        elif isinstance(node, list):
            for item in node:
                result = find_segments_key(item)
                if result:
                    return result
        return []

    return find_segments_key(ast_nodes)


def find_stmts_by_ident(ast: dict, variable_name: list):
    def recursive_search(node):
        if isinstance(node, dict):
            if "stmts" in node:
                for stmt in node["stmts"]:
                    result = recursive_search(stmt)
                    if result:
                        return stmt
            if "ident" in node and node["ident"] == variable_name:
                return node
            for key, value in node.items():
                result = recursive_search(value)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = recursive_search(item)
                if result:
                    return result
        return None

    return recursive_search(ast)


def find_stmts(ast: dict):
    matched_stmts = []

    def recursive_search(node):
        if isinstance(node, dict):
            if "stmts" in node:
                matched_stmts.extend(node["stmts"])
            for key, value in node.items():
                recursive_search(value)
        elif isinstance(node, list):
            for item in node:
                recursive_search(item)

    recursive_search(ast)
    return matched_stmts
