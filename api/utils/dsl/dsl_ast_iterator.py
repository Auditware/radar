class ASTNodeListGroup:
    def __init__(self, node_lists):
        self.node_lists = node_lists if isinstance(node_lists, list) else [node_lists]

    def __getattr__(self, name):
        def method(*args, **kwargs):
            results = []
            for node_list in self.node_lists:
                method = getattr(node_list, name, None)
                if method:
                    result = method(*args, **kwargs)
                    if isinstance(result, ASTNodeList):
                        results.extend(result.nodes)
                    elif result is not None:
                        results.append(result)
            return ASTNodeList(results)

        return method

    def __iter__(self):
        return iter(self.node_lists)

    def __len__(self):
        return len(self.node_lists)

    def to_result(self):
        return [node_list.to_result() for node_list in self.node_lists]

    def first(self):
        return self.node_lists[0] if self.node_lists else self.exit_on_none()

    def exit_on_none(self):
        if not self.node_lists:
            raise StopIteration("No node lists found")
        return self

    def exit_on_value(self):
        if self.node_lists:
            raise StopIteration("Node lists found")
        return self


class ASTNodeList:
    def __init__(self, nodes):
        self.nodes = nodes if isinstance(nodes, list) else [nodes]

    def __getattr__(self, name):
        def method(*args, **kwargs):
            results = []
            for node in self.nodes:
                node_method = getattr(node, name, None)
                if node_method:
                    result = node_method(*args, **kwargs)
                    if isinstance(result, list):
                        results.extend(result)
                    elif isinstance(result, ASTNodeList):
                        results.extend(result.nodes)
                    elif result is not None:
                        results.append(result)
            return ASTNodeList(results)

        return method

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def to_result(self):
        return [node.to_result() for node in self.nodes]

    def first(self):
        return self.nodes[0] if self.nodes else self.exit_on_none()

    def exit_on_none(self):
        if not self.nodes:
            raise StopIteration("No nodes found")
        return self

    def exit_on_value(self):
        if self.nodes:
            raise StopIteration("Nodes found")
        return self


class ASTNode:
    def __init__(self, node=None, access_path="", metadata={}):
        if node:
            self.src = node.get("src")
            self.ident = node.get("ident")
        else:
            self.src = None
            self.ident = "root"
        self.access_path = access_path
        self.metadata = metadata
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def to_result(self):
        return {
            "src": self.src,
            "ident": self.ident,
            "access_path": self.access_path,
            "metadata": self.metadata,
            "children": [child.to_result() for child in self.children],
            "parent": self.parent.ident if self.parent else None,
        }

    def find_by_parent(self, parent_ident: str) -> ASTNodeList:
        results = []
        if self.parent and self.parent.ident == parent_ident:
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_parent(parent_ident))
        return ASTNodeList(results)

    def find_chained_calls(self, *idents: tuple[str, ...]) -> ASTNodeListGroup:
        matches = []

        def recurse(node, idents):
            for i in range(len(node.children) - len(idents) + 1):
                if all(
                    node.children[i + j].ident == idents[j] for j in range(len(idents))
                ):
                    matches.append(ASTNodeList(node.children[i : i + len(idents)]))
            for child in node.children:
                recurse(child, idents)

        recurse(self, idents)
        return ASTNodeListGroup(matches)

    def find_by_access_path(self, access_path: str, keyword: str) -> ASTNodeList:
        index = access_path.rfind(keyword)
        if index != -1:
            truncated_path = access_path[: index + len(keyword)]
        else:
            truncated_path = access_path

        matching_nodes = []

        def recurse(node):
            if (
                truncated_path in node.access_path
                and node.access_path != truncated_path
            ):
                matching_nodes.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matching_nodes)

    def find_comparisons(self, ident1: str, ident2: str):
        comparisons = []

        def traverse(node):
            if not node:
                return

            if (
                "cond.binary.left" in node.access_path
                or "cond.binary.right" in node.access_path
            ):
                truncated_path = (
                    node.access_path.split(".cond.binary")[0] + ".cond.binary"
                )
                if "cond.binary.left" in node.access_path:
                    left_path = truncated_path + ".right"
                    right_node = find_node_by_access_path(left_path)
                    if right_node and check_conditions(
                        node, right_node, ident1, ident2
                    ):
                        comparisons.append(ASTNodeList([node, right_node]))
                elif "cond.binary.right" in node.access_path:
                    right_path = truncated_path + ".left"
                    left_node = find_node_by_access_path(right_path)
                    if left_node and check_conditions(left_node, node, ident1, ident2):
                        comparisons.append(ASTNodeList([left_node, node]))

            for child in node.children:
                traverse(child)

        def find_node_by_access_path(access_path):
            matching_node = None

            def recurse(node):
                nonlocal matching_node
                if access_path in node.access_path:
                    matching_node = node
                    return
                for child in node.children:
                    recurse(child)

            recurse(self)
            return matching_node

        def check_conditions(left_node, right_node, ident1, ident2):
            return (
                check_ident(left_node, ident1) and check_ident(right_node, ident2)
            ) or (check_ident(left_node, ident2) and check_ident(right_node, ident1))

        def check_ident(node, ident):
            if not node:
                return False
            if node.ident == ident:
                return True
            for child in node.children:
                if check_ident(child, ident):
                    return True
            return False

        traverse(self)
        return ASTNodeList(comparisons)

    def find_comparison_to_any(self, ident: str):
        comparisons = []

        def traverse(node):
            if not node:
                return

            if (
                "cond.binary.left" in node.access_path
                or "cond.binary.right" in node.access_path
                or "cond.unary" in node.access_path
            ):
                if check_ident(node, ident):
                    comparisons.append(node)

            for child in node.children:
                traverse(child)

        def check_ident(node, ident):
            if not node:
                return False
            if node.ident == ident:
                return True
            for child in node.children:
                if check_ident(child, ident):
                    return True
            return False

        traverse(self)
        return ASTNodeList(comparisons)

    def find_negative_of_operation(self, operation_name: str, *args: tuple) -> ASTNodeList:
        operation = getattr(self, operation_name)
        operation_results = operation(*args)
        operation_nodes = {node for pair in operation_results for node in pair}
        non_operation_nodes = []

        def traverse(node):
            if node not in operation_nodes:
                non_operation_nodes.append(node)
            for child in node.children:
                traverse(child)

        traverse(self)
        return ASTNodeList(non_operation_nodes)

    def find_functions_by_names(self, *function_names: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def find_function(node):
            if isinstance(node, ASTNode):
                if node.ident in function_names:
                    matching_nodes.append(node)
                for child in node.children:
                    find_function(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    find_function(value)
            elif isinstance(node, list):
                for item in node:
                    find_function(item)

        find_function(self)
        return ASTNodeList(matching_nodes)

    def find_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def search_nodes(node):
            if isinstance(node, ASTNode):
                if node.ident in idents:
                    matching_nodes.append(node)
                for child in node.children:
                    search_nodes(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        search_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    search_nodes(item)

        search_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_method_calls(self, caller: str, method: str) -> ASTNodeList:
        matching_nodes = []

        def recurse(node):
            if isinstance(node, ASTNode):
                if node.access_path.endswith("method_call") and node.ident == method:
                    if node.children and node.children[0].ident == caller:
                        matching_nodes.append(node)
                for child in node.children:
                    recurse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    recurse(value)
            elif isinstance(node, list):
                for item in node:
                    recurse(item)

        recurse(self)
        return ASTNodeList(matching_nodes)

    def find_assignments(self, ident: str, value_ident: str) -> ASTNodeList:
        assignments = []

        def traverse(node):
            if not node:
                return

            if node.ident == ident and ".assign.left" in node.access_path:
                assignment_path = node.access_path.split(".assign.left")[0] + ".assign"
                right_node = find_node_by_access_path(assignment_path + ".right")
                if right_node and check_conditions(node, right_node, value_ident):
                    assignments.append(ASTNodeList([node, right_node]))

            for child in node.children:
                traverse(child)

        def find_node_by_access_path(access_path):
            matching_node = None

            def recurse(node):
                nonlocal matching_node
                if access_path in node.access_path:
                    matching_node = node
                    return
                for child in node.children:
                    recurse(child)

            recurse(self)
            return matching_node

        def check_conditions(left_node, right_node, value_ident):
            left_access_path = left_node.access_path.rsplit(".assign.left", 1)[0]
            right_access_path = right_node.access_path.rsplit(".assign.right", 1)[0]
            return left_access_path == right_access_path and right_node.ident == str(
                value_ident
            )

        traverse(self)
        return ASTNodeList(assignments)

    def find_mutables(self) -> ASTNodeList:
        mutables = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if node and node.metadata.get("mut") is True:
                    mutables.append(node)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(mutables)

    def find_account_typed_nodes(self, ident: str) -> ASTNodeList:
        matches = []

        def ends_with_ty_path_segments(access_path):
            parts = access_path.split(".")
            segments_index = -1
            for i in range(len(parts)):
                if parts[i] == "ty" and i + 1 < len(parts) and parts[i + 1] == "path":
                    segments_index = i + 2
                    break
            if segments_index == -1:
                return False
            while segments_index < len(parts) and (
                parts[segments_index].startswith("segments[")
                or parts[segments_index] == "segments"
            ):
                segments_index += 1
            return segments_index == len(parts)

        def traverse(node):
            if isinstance(node, ASTNode):
                if ends_with_ty_path_segments(node.access_path):
                    if node.parent.ident == ident:
                        matches.append(node.parent)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(matches)

    def find_member_accesses(self, ident: str) -> ASTNodeList:
        member_accesses = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if node and node.ident == ident and "tokens" in node.access_path:
                    member_accesses.append(node)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(member_accesses)


def parse_prime_nodes(ast, access_path="", parent=None) -> list:
    nodes = []
    if isinstance(ast, dict):
        if "src" in ast and "ident" in ast:
            metadata = {}
            if "mut" in ast:
                metadata["mut"] = ast["mut"]
            node = ASTNode(ast, access_path, metadata)
            node.parent = parent
            nodes.append(node)
            parent = node
        # Mutable but no ident edge case, corelate a mutable statement with the closest ident
        elif "mut" in ast:
            metadata = {"mut": ast["mut"]}

            def find_ident_src_node(sub_data, sub_access_path):
                if isinstance(sub_data, dict):
                    if "src" in sub_data and "ident" in sub_data:
                        return ASTNode(sub_data, sub_access_path, metadata)
                    for key, value in sub_data.items():
                        new_path = (
                            f"{sub_access_path}.{key}" if sub_access_path else key
                        )
                        result = find_ident_src_node(value, new_path)
                        if result:
                            return result
                elif isinstance(sub_data, list):
                    for i, item in enumerate(sub_data):
                        new_path = f"{sub_access_path}[{i}]"
                        result = find_ident_src_node(item, new_path)
                        if result:
                            return result
                return None

            node = find_ident_src_node(ast, access_path)
            if node:
                node.parent = parent
                nodes.append(node)
                parent = node

        for key, value in ast.items():
            new_path = f"{access_path}.{key}" if access_path else key
            nodes.extend(parse_prime_nodes(value, new_path, parent))
    elif isinstance(ast, list):
        for i, item in enumerate(ast):
            new_path = f"{access_path}[{i}]"
            nodes.extend(parse_prime_nodes(item, new_path, parent))
    return nodes


def map_hierarchy(prime_nodes: list):
    path_to_node = {node.access_path: node for node in prime_nodes}
    assigned_children = set()
    for node in prime_nodes:
        if node.access_path in assigned_children:
            continue
        parent_path = ".".join(node.access_path.split(".")[:-1])
        while parent_path:
            parent_node = path_to_node.get(parent_path)
            if parent_node:
                parent_node.add_child(node)
                assigned_children.add(node.access_path)
                break
            parent_path = ".".join(parent_path.split(".")[:-1])


def parse_ast(ast: dict) -> dict:
    sources = {}
    prime_nodes = parse_prime_nodes(ast)

    for node in prime_nodes:
        source = node.src.get("file") if node.src else "unknown"
        if source not in sources:
            sources[source] = []
        sources[source].append(node)

    roots = {}
    for source, nodes in sources.items():
        map_hierarchy(nodes)
        root = ASTNode()
        for node in nodes:
            if not node.parent:
                root.add_child(node)
        roots[source] = root

    return roots
