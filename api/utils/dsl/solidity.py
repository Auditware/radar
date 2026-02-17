from dataclasses import dataclass
import re
from utils.dsl.dsl_ast_iterator import ASTNode, ASTNodeList, ASTNodeListGroup


@dataclass
class SolidityASTNode(ASTNode):
    file: str = None
    node_type: str = None
    src_calculated: str = None

    def __init__(
        self, node=None, file=None, src_calculated=None, access_path="", metadata={}
    ):
        super().__init__(node, access_path, metadata)
        self.file = file
        self.src_calculated = src_calculated
        if node:
            self.node_type = node.get("nodeType")

    def to_result(self):
        result = {
            "node_type": self.node_type,
            "file": self.file,
            "src_calculated": self.src_calculated,
        }
        result.update(super().to_result())
        result.update(
            {
                "parent": self.parent.node_type if self.parent else None,
            }
        )
        return result

    def find_all_functions(self) -> ASTNodeList:
        function_nodes = []

        def find_functions(node):
            if isinstance(node, ASTNode):
                if node.node_type == "FunctionDefinition":
                    function_nodes.append(node)
                for child in node.children:
                    find_functions(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    find_functions(value)
            elif isinstance(node, list):
                for item in node:
                    find_functions(item)

        find_functions(self)
        return ASTNodeList(function_nodes)

    def find_modifiers_by_names(self, *modifier_names: tuple[str, ...]) -> ASTNodeList:
        modifier_nodes = []

        def find_modifiers(node):
            if isinstance(node, ASTNode):
                if node.access_path.endswith("modifierName"):
                    if hasattr(node, "metadata") and "name" in node.metadata:
                        if node.metadata["name"] in modifier_names:
                            modifier_nodes.append(node)
                for child in node.children:
                    find_modifiers(child)

            elif isinstance(node, dict):
                for key, value in node.items():
                    if key.endswith(".modifierName") and isinstance(value, dict):
                        if (
                            "name" in value.get("metadata", {})
                            and value["metadata"]["name"] in modifier_names
                        ):
                            modifier_nodes.append(value)
                    find_modifiers(value)

            elif isinstance(node, list):
                for item in node:
                    find_modifiers(item)

        find_modifiers(self)
        return ASTNodeList(modifier_nodes)

    def find_external_calls(self) -> ASTNodeList:
        low_level_call_nodes = []
        valid_member_names = {"call", "delegatecall", "send", "transfer"}

        def find_call(node):
            if isinstance(node, ASTNode):
                if node.node_type == "MemberAccess":
                    if (
                        hasattr(node, "parent")
                        and node.parent.node_type == "FunctionCallOptions"
                    ):
                        if (
                            hasattr(node, "metadata")
                            and node.metadata.get("memberName") in valid_member_names
                        ):
                            low_level_call_nodes.append(node)
                for child in node.children:
                    find_call(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    find_call(value)
            elif isinstance(node, list):
                for item in node:
                    find_call(item)

        find_call(self)
        return ASTNodeList(low_level_call_nodes)

    def find_functions_with_address_assignments(self) -> ASTNodeList:
        function_nodes_with_address = []

        def find_functions_with_address(node):
            if isinstance(node, ASTNode):
                if (
                    node.node_type == "FunctionDefinition"
                    and node.metadata.get("stateMutability") != "view"
                ):
                    has_address_assignment = False

                    def find_address_assignments(sub_node):
                        nonlocal has_address_assignment
                        if isinstance(sub_node, ASTNode):
                            if sub_node.node_type == "Assignment":
                                if sub_node.metadata.get("type_string") == "address":
                                    has_address_assignment = True
                            for child in sub_node.children:
                                find_address_assignments(child)
                        elif isinstance(sub_node, dict):
                            for value in sub_node.values():
                                find_address_assignments(value)
                        elif isinstance(sub_node, list):
                            for item in sub_node:
                                find_address_assignments(item)

                    find_address_assignments(node)

                    if has_address_assignment:
                        function_nodes_with_address.append(node)

                for child in node.children:
                    find_functions_with_address(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_functions_with_address(value)
            elif isinstance(node, list):
                for item in node:
                    find_functions_with_address(item)

        find_functions_with_address(self)
        return ASTNodeList(function_nodes_with_address)

    def find_setters_and_constructors(self) -> ASTNodeList:
        setter_and_constructor_nodes = []

        def find_setters_and_constructors_in_node(node):
            if isinstance(node, ASTNode):
                if node.node_type == "FunctionDefinition":
                    if (
                        node.metadata.get("kind") == "constructor"
                        or node.metadata.get("name", "").startswith("init")
                        or node.metadata.get("name", "").startswith("set")
                    ):
                        setter_and_constructor_nodes.append(node)

                for child in node.children:
                    find_setters_and_constructors_in_node(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_setters_and_constructors_in_node(value)
            elif isinstance(node, list):
                for item in node:
                    find_setters_and_constructors_in_node(item)

        find_setters_and_constructors_in_node(self)
        return ASTNodeList(setter_and_constructor_nodes)

    def find_nodes_by_names(self, *names: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def find_nodes(node):
            if isinstance(node, ASTNode):
                if node.metadata.get("name") in names:
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_nodes_by_type_strings(self, *patterns: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def match_pattern(value):
            # Check if the value matches any of the patterns (either substring or regex)
            for pattern in patterns:
                if re.search(pattern, value) or pattern in value:
                    return True
            return False

        def find_nodes(node):
            if isinstance(node, ASTNode):
                type_string = node.metadata.get("type_string")
                if type_string and match_pattern(type_string):
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_nodes_by_type_identifiers(self, *patterns: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def match_pattern(value):
            # Check if the value matches any of the patterns (either substring or regex)
            for pattern in patterns:
                if re.search(pattern, value) or pattern in value:
                    return True
            return False

        def find_nodes(node):
            if isinstance(node, ASTNode):
                type_identifier = node.metadata.get("type_identifier")
                if type_identifier and match_pattern(type_identifier):
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_comparisons_between(self, *names: tuple[str, ...]) -> ASTNodeList:
        matching_comparisons = []

        def find_comparisons(node):
            if isinstance(node, ASTNode):
                # Check if the node is a comparison with operator "=="
                if node.metadata.get("operator") == "==":
                    # Check if both children (leftExpression and rightExpression) match the provided names
                    children_names = [
                        child.metadata.get("name")
                        for child in node.children
                        if child.metadata.get("name") is not None
                    ]
                    if set(names).issubset(set(children_names)):
                        matching_comparisons.append(node)

                # Recursively search in the children nodes
                for child in node.children:
                    find_comparisons(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_comparisons(value)
            elif isinstance(node, list):
                for item in node:
                    find_comparisons(item)

        find_comparisons(self)
        return ASTNodeList(matching_comparisons)

    def find_nodes_by_types(self, *types: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def find_nodes(node):
            if isinstance(node, ASTNode):
                if node.node_type in types:
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_nodes_by_member_names(
        self, *member_names: tuple[str, ...]
    ) -> ASTNodeList:
        matching_nodes = []

        def find_nodes(node):
            if isinstance(node, ASTNode):
                if node.metadata.get("memberName") in member_names:
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_nodes_by_operators(self, *operators: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def find_nodes(node):
            if isinstance(node, ASTNode):
                if node.metadata.get("operator") in operators:
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_nodes_by_metadata_key(self, key_name: str, *patterns: tuple[str, ...]) -> ASTNodeList:
        matching_nodes = []

        def match_pattern(value):
            for pattern in patterns:
                if re.search(pattern, value) or pattern in value:
                    return True
            return False

        def find_nodes(node):
            if isinstance(node, ASTNode):
                # Retrieve the metadata value associated with key_name
                metadata_value = node.metadata.get(key_name)
                if metadata_value and match_pattern(metadata_value):
                    matching_nodes.append(node)

                for child in node.children:
                    find_nodes(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        find_nodes(self)
        return ASTNodeList(matching_nodes)

    def find_similar_function_definitions(self):
        similar_functions = []

        def find_nodes(node):
            if isinstance(node, ASTNode):
                if node.node_type == "FunctionDefinition" and node.children:
                    function_nodes.append(node)
                for child in node.children:
                    find_nodes(child)
            elif isinstance(node, dict):
                if node.get("node_type") == "FunctionDefinition" and node.get("children"):
                    function_nodes.append(node)
                for value in node.values():
                    find_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    find_nodes(item)

        def node_type_sequence(node):
            sequence = []

            def traverse(node):
                if isinstance(node, ASTNode):
                    if hasattr(node, "node_type"):
                        sequence.append(node.node_type)
                    for child in node.children:
                        traverse(child)
                elif isinstance(node, dict):
                    if "node_type" in node:
                        sequence.append(node["node_type"])
                    for value in node.get("children", []):
                        traverse(value)
                elif isinstance(node, list):
                    for item in node:
                        traverse(item)

            traverse(node)
            return sequence

        function_nodes = []
        find_nodes(self)

        for i, func_node1 in enumerate(function_nodes):
            seq1 = node_type_sequence(func_node1)
            for j, func_node2 in enumerate(function_nodes[i + 1:], start=i + 1):
                seq2 = node_type_sequence(func_node2)
                if seq1 == seq2:
                    if func_node1 not in similar_functions:
                        similar_functions.append(func_node1)
                    if func_node2 not in similar_functions:
                        similar_functions.append(func_node2)

        return ASTNodeList(similar_functions)

    def find_functions_by_name_patterns(self, *patterns: tuple[str, ...]) -> ASTNodeList:
        matching_function_nodes = []

        def match_pattern(value: str) -> bool:
            for pattern in patterns:
                if any(re.search(p, value) or p in value for p in pattern):
                    return True
            return False

        def find_functions(node):
            if isinstance(node, ASTNode):
                if node.node_type == "FunctionDefinition":
                    function_name = node.metadata.get("name", "")
                    if function_name and match_pattern(function_name):
                        matching_function_nodes.append(node)

                for child in node.children:
                    find_functions(child)

            elif isinstance(node, dict):
                for value in node.values():
                    find_functions(value)
            elif isinstance(node, list):
                for item in node:
                    find_functions(item)

        find_functions(self)
        return ASTNodeList(matching_function_nodes)


def serialize_solidity_ast(ast, parent=None):
    def serialize_solidity_file_ast(ast, parent=None, file=None, access_path=""):
        nodes = []

        # Match - include nodes that has src and nodeType keys
        if isinstance(ast, dict):
            if "src" in ast and "nodeType" in ast:
                # Metadatas
                metadata = {}
                fields_to_update = {
                    "name": ast.get(
                        "name"
                    ),  # Name of the variable, function, or member
                    "operator": ast.get(
                        "operator"
                    ),  # Operator used in an expression (e.g., '+', '-', '*')
                    "kind": ast.get(
                        "kind"
                    ),  # Kind of the AST node (e.g., function, variable, expression)
                    "value": ast.get("value"),
                    "visibility": ast.get(
                        "visibility"
                    ),  # Visibility of the function/variable (e.g., public, private)
                    "stateMutability": ast.get(
                        "stateMutability"
                    ),  # Mutability state of a function (e.g., pure, view)
                    "mutability": ast.get(
                        "mutability"
                    ),  # General mutability of the node (e.g., mutable, immutable)
                    "virtual": ast.get(
                        "virtual"
                    ),  # Indicates if the function is virtual (can be overridden)
                    "isConstant": ast.get(
                        "isConstant"
                    ),  # Indicates if the value is a constant
                    "constant": ast.get(
                        "constant"
                    ),  # Legacy field for constant functions/variables (deprecated)
                    "isPure": ast.get(
                        "isPure"
                    ),  # Indicates if the function is pure (does not read or modify state)
                    "stateVariable": ast.get(
                        "stateVariable"
                    ),  # Indicates if the variable is a state variable
                    "isLValue": ast.get(
                        "isLValue"
                    ),  # Indicates if the expression is an L-value (can be assigned)
                    "lValueRequested": ast.get(
                        "lValueRequested"
                    ),  # Indicates if an L-value was requested
                    "memberName": ast.get(
                        "memberName"
                    ),  # Name of the member in a member access (e.g., `foo` in `object.foo`)
                    "type_identifier": ast.get("typeDescriptions", {}).get(
                        "typeIdentifier"
                    ),  # Unique identifier for the type
                    "type_string": ast.get("typeDescriptions", {}).get(
                        "typeString"
                    ),  # Human-readable string of the type
                    "absolutePath": ast.get("absolutePath"), # Absolute path to file
                    "literals": ast.get("literals")
                }
                metadata.update(
                    {k: v for k, v in fields_to_update.items() if v is not None}
                )

                node = SolidityASTNode(
                    node=ast,
                    file=file,
                    access_path=access_path,
                    metadata=metadata,
                    src_calculated=ast.get("src_calculated"),
                )
                node.parent = parent
                nodes.append(node)
                parent = node

            # Look deeper
            for key, value in ast.items():
                new_access_path = f"{access_path}.{key}" if access_path else key
                nodes.extend(
                    serialize_solidity_file_ast(
                        value, parent, file=file, access_path=new_access_path
                    )
                )

        # Look deeper
        elif isinstance(ast, list):
            for index, item in enumerate(ast):
                new_access_path = f"{access_path}[{index}]"
                nodes.extend(
                    serialize_solidity_file_ast(
                        item, parent, file=file, access_path=new_access_path
                    )
                )

        return nodes

    nodes = []

    if isinstance(ast, dict):
        for source, ast in ast.items():
            nodes.extend(
                serialize_solidity_file_ast(ast, parent, file=source, access_path="")
            )

    return nodes


def parse_solidity_ast(ast: dict) -> dict:
    sources_ast = ast.get("sources", {})
    
    nodes = serialize_solidity_ast(sources_ast)
    
    sources = {}
    for node in nodes:
        source = node.file if node.file else "unknown"
        if source not in sources:
            sources[source] = []
        sources[source].append(node)
    
    roots = {}
    for source, source_nodes in sources.items():
        path_to_node = {node.access_path: node for node in source_nodes}
        assigned_children = set()
        for node in source_nodes:
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
        
        root = SolidityASTNode()
        for node in source_nodes:
            if not node.parent:
                root.add_child(node)
        
        roots[source] = root
    
    return roots
