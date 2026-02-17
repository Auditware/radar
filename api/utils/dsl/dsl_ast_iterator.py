from functools import wraps
from dataclasses import dataclass, field
from typing import List, Optional
import json


def dsl_log(func):
    """Decorator for logging DSL function calls and their results.

    Args:
        func: The function to be decorated.

    Returns:
        Wrapped function that logs its execution details.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        args_str = ", ".join(
            str(arg)[:50] + "..." if len(str(arg)) > 50 else str(arg)
            for arg in args[1:]
        )
        kwargs_str = ", ".join(
            f"{k}={str(v)[:30] + '...' if len(str(v)) > 30 else str(v)}"
            for k, v in kwargs.items()
        )
        params = ", ".join(filter(None, [args_str, kwargs_str]))

        try:
            result = func(*args, **kwargs)

            node_count = 0
            if hasattr(result, "__len__"):
                node_count = len(result)
            elif result is not None:
                node_count = 1

            # Special handling for exit methods
            if func_name == "exit_on_none":
                print(
                    f"[d] [dsl_log] {func_name}({params}) -> continued ({node_count} nodes)"
                )  # should always be >1
            elif func_name == "exit_on_value":
                print(
                    f"[d] [dsl_log] {func_name}({params}) -> continued ({node_count} nodes)"
                )  # should always be 0
            else:
                print(f"[d] [dsl_log] {func_name}({params}) -> {node_count} nodes")
            return result
        except StopIteration as e:
            print(f"[d] [dsl_log] {func_name}({params}) -> StopIteration: {e}")
            raise

    return wrapper


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

    def __getitem__(self, index):
        return self.node_lists[index]

    @dsl_log
    def to_result(self):
        """Convert the node list group to result format.

        Returns:
            List of result dictionaries for each node list in the group.
        """
        return [node_list.to_result() for node_list in self.node_lists]

    @dsl_log
    def first(self):
        """Get the first node list in the group.

        Returns:
            The first node list in the group, or raises StopIteration if empty.
        """
        return self.node_lists[0] if self.node_lists else self.exit_on_none()

    @dsl_log
    def exit_on_none(self):
        """Exit with StopIteration if no node lists are found.

        Returns:
            Self if node lists exist.

        Raises:
            StopIteration: If no node lists are found.
        """
        if not self.node_lists:
            raise StopIteration("No node lists found")
        return self

    @dsl_log
    def exit_on_value(self):
        """Exit with StopIteration if node lists are found.

        Returns:
            Self if no node lists exist.

        Raises:
            StopIteration: If node lists are found.
        """
        if self.node_lists:
            raise StopIteration("Node lists found")
        return self

    def to_raw_ast_debug(self):
        """Print debug information for the node list group.

        Returns:
            Self for method chaining.
        """
        result_data = []
        for i, node_list in enumerate(self.node_lists):
            group_data = []
            for node in node_list.nodes:
                group_data.append(node.to_result())
            result_data.append(group_data)

        print()
        print("Raw AST Node List Group Debug:")
        print(json.dumps(result_data, indent=4, default=str))
        print()
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

    def __getitem__(self, index):
        return self.nodes[index]

    @dsl_log
    def to_result(self):
        """Convert the node list to result format.

        Returns:
            List of result dictionaries for each node in the list.
        """
        return [node.to_result() for node in self.nodes]

    @dsl_log
    def first(self):
        """Get the first node in the list.

        Returns:
            The first node in the list, or raises StopIteration if empty.
        """
        return self.nodes[0] if self.nodes else self.exit_on_none()

    @dsl_log
    def exit_on_none(self):
        """Exit with StopIteration if no nodes are found.

        Returns:
            Self if nodes exist.

        Raises:
            StopIteration: If no nodes are found.
        """
        if not self.nodes:
            raise StopIteration("No nodes found")
        return self

    @dsl_log
    def exit_on_value(self):
        """Exit with StopIteration if nodes are found.

        Returns:
            Self if no nodes exist.

        Raises:
            StopIteration: If nodes are found.
        """
        if self.nodes:
            raise StopIteration("Nodes found")
        return self

    def to_raw_ast_debug(self):
        """Print debug information for the node list.

        Returns:
            Self for method chaining.
        """
        result_data = [node.to_result() for node in self.nodes]

        print()
        print("Raw AST Node List Debug:")
        print(json.dumps(result_data, indent=4, default=str))
        print()
        return self


@dataclass
class ASTNode:
    src: Optional[str | dict] = None
    access_path: str = ""
    metadata: dict = field(default_factory=dict)
    children: List["ASTNode"] = field(default_factory=list)
    parent: Optional["ASTNode"] = None
    root: bool = False

    def __init__(self, node=None, access_path="", metadata={}):
        if node:
            self.src = node.get("src")
        else:
            self.root = True

        self.metadata = metadata
        self.children = []
        self.access_path = access_path

    def add_child(self, child: "ASTNode"):
        """Add a child node to this node.

        Args:
            child: The child ASTNode to add.
        """
        child.parent = self
        self.children.append(child)

    def to_result(self):
        """Convert the node to result format.

        Returns:
            Dictionary representation of the node including source, children, access path, and metadata.
        """
        return {
            "src": self.src,
            "children": [child.to_result() for child in self.children],
            "access_path": self.access_path,
            "metadata": self.metadata,
        }


@dataclass
class RustASTNode(ASTNode):
    ident: str = "root"

    def __init__(self, node=None, access_path="", metadata={}):
        super().__init__(node, access_path, metadata)
        if node:
            self.ident = node.get("ident")
        else:
            self.ident = "root"
            self.root = True

    def to_result(self):
        """Convert the Rust AST node to result format.

        Returns:
            Dictionary representation of the node including identifier and parent information.
        """
        result = super().to_result()
        result.update(
            {
                "ident": self.ident,
                "parent": self.parent.ident if self.parent else None,
            }
        )
        return result

    def to_raw_ast_debug(self):
        """Print debug information for the Rust AST node.

        Returns:
            Self for method chaining.
        """
        result = super().to_result()
        result.update(
            {
                "ident": self.ident,
                "parent": self.parent.ident if self.parent else None,
            }
        )
        print()
        print("Raw AST Node Debug:")
        print(json.dumps(result, indent=4, default=str))
        print()
        return self

    @dsl_log
    def find_by_parent(self, parent_ident: str) -> ASTNodeList:
        """Find all nodes that have a specific parent identifier.

        Args:
            parent_ident: The identifier of the parent node to search for.

        Returns:
            ASTNodeList of nodes that have the specified parent identifier.
        """
        results = []
        if self.parent and self.parent.ident == parent_ident:
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_parent(parent_ident))
        return ASTNodeList(results)

    @dsl_log
    def find_by_child(self, child_ident: str) -> ASTNodeList:
        """Find all nodes that have a specific child identifier.

        Args:
            child_ident: The identifier of the child node to search for.

        Returns:
            ASTNodeList of nodes that have a child with the specified identifier.
        """
        matches = []

        def recurse(node):
            if any(child.ident == child_ident for child in node.children):
                matches.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matches)

    @dsl_log
    def find_chained_calls(self, *idents: tuple[str, ...]) -> ASTNodeListGroup:
        """Find sequences of chained method calls with specific identifiers.

        Args:
            *idents: Variable number of identifiers that should appear in sequence as chained calls.

        Returns:
            ASTNodeListGroup containing lists of nodes that match the chained call pattern.
        """
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

    @dsl_log
    def find_by_access_path(self, access_path_part: str) -> ASTNodeList:
        """Find nodes that contain a specific part in their access path.

        Args:
            access_path_part: The partial access path string to search for.

        Returns:
            ASTNodeList of nodes whose access path contains the specified part.
        """
        matching_nodes = []

        def recurse(node):
            if access_path_part in node.access_path:
                matching_nodes.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_macro_attribute_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList:
        """Find macro attributes by their identifier names.

        Args:
            *idents: Variable number of identifiers to search for in macro attributes.

        Returns:
            ASTNodeList of nodes that are macro attributes with the specified identifiers.
        """
        matching_nodes = []

        def search_nodes(node):
            if isinstance(node, ASTNode):
                if node.ident in idents and ".meta.list.tokens" in node.access_path:
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

    @dsl_log
    def find_by_similar_access_path(
        self, access_path: str, stop_keyword: str
    ) -> ASTNodeList:
        """Find nodes with access paths similar to the given path, truncated at a stop keyword.

        Args:
            access_path: The base access path to compare against.
            stop_keyword: The keyword where the path should be truncated for comparison.

        Returns:
            ASTNodeList of nodes with similar access paths to the truncated base path.
        """
        index = access_path.rfind(stop_keyword)
        if index != -1:
            truncated_path = access_path[: index + len(stop_keyword)]
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

    @dsl_log
    def find_comparisons_between(self, ident1: str, ident2: str):
        """Find binary comparison operations between two specific identifiers.

        Args:
            ident1: The first identifier to look for in comparisons.
            ident2: The second identifier to look for in comparisons.

        Returns:
            ASTNodeList of comparison nodes that involve both specified identifiers.
        """
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

    @dsl_log
    def find_comparison_involving(self, ident: str):
        """Find any comparison operations that involve a specific identifier.

        Args:
            ident: The identifier to search for in comparison operations.

        Returns:
            ASTNodeList of comparison nodes that involve the specified identifier.
        """
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

    @dsl_log
    def find_negative_of_operation(
        self, operation_name: str, *args: tuple
    ) -> ASTNodeList:
        """Find nodes that are NOT involved in a specific operation.

        Args:
            operation_name: The name of the operation method to exclude.
            *args: Arguments to pass to the operation method.

        Returns:
            ASTNodeList of nodes that are not part of the specified operation results.
        """
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

    @dsl_log
    def find_functions_by_names(self, *function_names: tuple[str, ...]) -> ASTNodeList:
        """Find function nodes by their names.

        Args:
            *function_names: Variable number of function names to search for.

        Returns:
            ASTNodeList of function nodes with the specified names.
        """
        matching_nodes = []

        def find_function(node):
            if isinstance(node, ASTNode):
                # Check if this is a function node by looking for .fn at the end of access path
                # and the ident matches one of the function names
                if node.ident in function_names and node.access_path.endswith(".fn"):
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

    @dsl_log
    def find_all_functions(self) -> ASTNodeList:
        """Find all function nodes in the AST.

        Returns:
            ASTNodeList of all function nodes found.
        """
        matching_nodes = []

        def find_function(node):
            if isinstance(node, ASTNode):
                # Check if this is a function node by looking for .fn at the end of access path
                if node.access_path.endswith(".fn"):
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

    @dsl_log
    def find_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList:
        """Find nodes by their identifier names.

        Args:
            *idents: Variable number of identifiers to search for.

        Returns:
            ASTNodeList of nodes with the specified identifiers.
        """
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

    @dsl_log
    def find_method_calls(self, caller: str, method: str) -> ASTNodeList:
        """Find method call nodes with specific caller and method names.

        Args:
            caller: The identifier of the object making the method call.
            method: The name of the method being called.

        Returns:
            ASTNodeList of method call nodes matching the caller and method criteria.
        """
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

    @dsl_log
    def find_assignments(self, ident: str, value_ident: str) -> ASTNodeList:
        """Find assignment operations between specific identifiers.

        Args:
            ident: The identifier being assigned to (left side of assignment).
            value_ident: The identifier being assigned from (right side of assignment).

        Returns:
            ASTNodeList of assignment nodes matching the specified identifiers.
        """
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

    @dsl_log
    def find_mutables(self) -> ASTNodeList:
        """Find all nodes that are marked as mutable.

        Returns:
            ASTNodeList of nodes that have the 'mut' metadata flag set to True.
        """
        mutables = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if hasattr(node, "metadata") and isinstance(node.metadata, dict):
                    if node.metadata.get("mut") is True:
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

    @dsl_log
    def find_account_typed_nodes(self, ident: str) -> ASTNodeList:
        """Find nodes that are typed as accounts with a specific identifier.

        Args:
            ident: The identifier to search for in account type definitions.

        Returns:
            ASTNodeList of nodes that are account-typed with the specified identifier.
        """
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

    @dsl_log
    def find_member_accesses(self, ident: str) -> ASTNodeList:
        """Find member access operations for a specific identifier.

        Args:
            ident: The identifier to search for in member access operations.

        Returns:
            ASTNodeList of nodes representing member accesses of the specified identifier.
        """
        member_accesses = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if (
                    node
                    and node.ident == ident
                    and (
                        "tokens" in node.access_path or "call.args" in node.access_path
                    )
                ):
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

    @dsl_log
    def find_binary_operations(self, *operators: tuple[str, ...]) -> ASTNodeList:
        """Find binary operations with specific operators.

        Args:
            *operators: Variable number of operator strings to search for (e.g., "*", "+", "-", "/").

        Returns:
            ASTNodeList of nodes that are involved in binary operations with the specified operators.
        """
        matching_nodes = []
        search_path_prefix = self.access_path if not self.root else ""
        
        all_nodes = getattr(self, "_all_nodes", [])
        if not all_nodes:
            all_nodes = [self]
        
        seen_binary_paths = set()
        for node in all_nodes:
            if search_path_prefix and not node.access_path.startswith(search_path_prefix):
                continue
            
            op = node.metadata.get("op")
            if op and op in operators:
                has_binary_child = False
                for child in node.children:
                    if child.access_path and ".binary." in child.access_path:
                        has_binary_child = True
                        break
                
                if has_binary_child:
                    binary_base_path = node.access_path
                    if binary_base_path not in seen_binary_paths:
                        matching_nodes.append(node)
                        seen_binary_paths.add(binary_base_path)

        return ASTNodeList(matching_nodes)


def serialize_rust_ast(ast, access_path="", parent=None) -> list:
    """Serialize a Rust AST into a list of RustASTNode objects.

    Args:
        ast: The AST data structure to serialize (dict or list).
        access_path: The current access path for nested elements (default: "").
        parent: The parent RustASTNode object (default: None).

    Returns:
        List of RustASTNode objects representing the serialized AST.
    """
    nodes = []
    if isinstance(ast, dict):
        # Match - include nodes that has src and ident keys
        if "src" in ast and "ident" in ast:
            metadata = {}
            if "mut" in ast:
                metadata["mut"] = ast["mut"]
            node = RustASTNode(ast, access_path, metadata)
            node.parent = parent
            nodes.append(node)
            parent = node

        # Mutable but no ident edge case, corelate a mutable statement with the closest ident
        elif "mut" in ast:
            metadata = {"mut": ast["mut"]}

            def find_ident_src_node(sub_data, sub_access_path):
                if isinstance(sub_data, dict):
                    # Match
                    if "src" in sub_data and "ident" in sub_data:
                        return RustASTNode(sub_data, sub_access_path, metadata)

                    # Look deeper
                    for key, value in sub_data.items():
                        new_path = (
                            f"{sub_access_path}.{key}" if sub_access_path else key
                        )
                        result = find_ident_src_node(value, new_path)
                        if result:
                            return result

                # Look deeper
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

        # Capture binary operator information
        if "op" in ast and parent:
            if not hasattr(parent, "metadata"):
                parent.metadata = {}
            parent.metadata["op"] = ast["op"]

        # Also capture operator from binary expressions (syn AST structure)
        if "binary" in ast and isinstance(ast["binary"], dict) and "op" in ast["binary"]:
            # Find the first ident node in the left side to use its src location
            def find_first_ident_node(data, path):
                if isinstance(data, dict):
                    if "src" in data and "ident" in data:
                        return (data, path)
                    for key, value in data.items():
                        result = find_first_ident_node(value, f"{path}.{key}" if path else key)
                        if result:
                            return result
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        result = find_first_ident_node(item, f"{path}[{i}]")
                        if result:
                            return result
                return None
            
            # Create a node for the binary operator
            left_result = find_first_ident_node(ast["binary"].get("left", {}), "")
            if left_result:
                left_node_data, _ = left_result
                binary_op = ast["binary"]["op"]
                binary_node_data = {
                    "src": left_node_data["src"],
                    "ident": binary_op
                }
                binary_node = RustASTNode(
                    binary_node_data,
                    f"{access_path}.binary",
                    {"op": binary_op}
                )
                binary_node.parent = parent
                nodes.append(binary_node)

        # Look deeper
        for key, value in ast.items():
            new_path = f"{access_path}.{key}" if access_path else key
            nodes.extend(serialize_rust_ast(value, new_path, parent))
    
    # Look deeper
    elif isinstance(ast, list):
        for i, item in enumerate(ast):
            new_path = f"{access_path}[{i}]"
            nodes.extend(serialize_rust_ast(item, new_path, parent))

    return nodes


def parse_ast(ast: dict, language: str = "rust") -> dict:
    """Parse an AST dictionary into organized source-based node hierarchies.

    Args:
        ast: The AST dictionary to parse.
        language: Programming language ('rust' or 'solidity'). Defaults to 'rust'.

    Returns:
        Dictionary mapping source file names to their root ASTNode objects.
    """
    if language == "solidity":
        from utils.dsl.solidity import parse_solidity_ast
        return parse_solidity_ast(ast)
    else:
        return parse_rust_ast(ast)


def parse_rust_ast(ast: dict) -> dict:
    """Parse Rust AST dictionary into organized source-based node hierarchies.

    Args:
        ast: The Rust AST dictionary to parse.

    Returns:
        Dictionary mapping source file names to their root RustASTNode objects.
    """
    sources = {}
    nodes = serialize_rust_ast(ast)

    for node in nodes:
        source = node.src.get("file") if node.src else "unknown"
        if source not in sources:
            sources[source] = []
        sources[source].append(node)

    roots = {}
    for source, nodes in sources.items():
        path_to_node = {node.access_path: node for node in nodes}
        assigned_children = set()
        for node in nodes:
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
        root = RustASTNode()
        root._all_nodes = nodes
        for node in nodes:
            node._all_nodes = nodes
            if not node.parent:
                root.add_child(node)
        roots[source] = root

    return roots
