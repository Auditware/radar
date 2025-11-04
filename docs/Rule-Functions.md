# Rule Functions Documentation

This page has descriptions about the core instance methods used by the abstraction functionality of the radar template rule syntax.

You can use these when you write new radar template rules and want to understand what pythonic ast searching capabilities are abstracted for you

For a deeper dive refer to the relevant part in the DSL that implements these functionalities: [api/utils/dsl/dsl_ast_iterator.py](https://github.com/Auditware/radar/blob/main/api/utils/dsl/dsl_ast_iterator.py)

See [How to write templates](https://github.com/auditware/radar/wiki/How-to-Write-Templates).

## Table of Contents

- [ASTNode Methods](#astnode-methods)
  - [to_result()](#to_result)
  - [find_by_parent()](#find_by_parent)
  - [find_by_child()](#find_by_child)
  - [find_chained_calls()](#find_chained_calls)
  - [find_by_access_path()](#find_by_access_path)
  - [find_by_similar_access_path()](#find_by_similar_access_path)
  - [find_comparisons_between()](#find_comparisons_between)
  - [find_comparison_involving()](#find_comparison_involving)
  - [find_negative_of_operation()](#find_negative_of_operation)
  - [find_functions_by_names()](#find_functions_by_names)
  - [find_by_names()](#find_by_names)
  - [find_method_calls()](#find_method_calls)
  - [find_assignments()](#find_assignments)
  - [find_mutables()](#find_mutables)
  - [find_account_typed_nodes()](#find_account_typed_nodes)
  - [find_member_accesses()](#find_member_accesses)
  - [to_raw_ast_debug()](#to_raw_ast_debug)
- [ASTNodeList, ASTNodeListGroup](#astnodelist-astnodelistgroup)
  - [first()](#first)
  - [to_result()](#to_result-1)
  - [exit_on_none()](#exit_on_none)
  - [exit_on_value()](#exit_on_value)
  - [to_raw_ast_debug()](#to_raw_ast_debug-1)

## ASTNode Methods

```python
to_result(self)
```

Converts the current node and its children into a dictionary format suitable for serialization and further processing as a finding result location.

<br />

```python
find_by_parent(self, parent_ident: str) -> ASTNodeList
```

Finds all nodes whose parent has the specified identifier and returns them as an ASTNodeList.

<br />

```python
find_by_child(self, child_ident: str) -> ASTNodeList
```

Finds all nodes whose child has the specified identifier and returns them as an ASTNodeList.

<br />

```python
find_chained_calls(self, *idents: tuple[str, ...]) -> ASTNodeListGroup
```

Finds sequences of sequential nodes matching the specified identifiers and returns them as an ASTNodeListGroup.

<br />

```python
find_by_access_path(self, access_path_part: str) -> ASTNodeList
```

Finds nodes whose access_path with the given portion of the access path string within it, and returns them as an ASTNodeList.

`access_path` is a value representing the sequence of AST nodes walked until indexing of the node, that did not get indexed (due to not being a prime node).


<br />

```python
find_by_similar_access_path(self, access_path: str, stop_keyword: str) -> ASTNodeList
```

Finds nodes whose access_path is identical to the one provided up until the stop_keyword, and returns them as an ASTNodeList.

`access_path` is a value representing the sequence of AST nodes walked until indexing of the node, that did not get indexed (due to not being a prime node).

<br />

```python
find_comparisons_between(self, ident1: str, ident2: str)
```

Finds binary comparisons between the specified identifiers within the AST and returns them as an ASTNodeList.

<br />

```python
find_comparison_involving(self, ident: str)
```

Finds any node involved in a comparison with the specified identifier and returns them as an ASTNodeList.

<br />

```python
find_negative_of_operation(self, operation_name: str, *args: tuple) -> ASTNodeList
```

Finds nodes that do not match the results of the specified operation and returns them as an ASTNodeList.

"operation" refers to an ASTNode instance method.

<br />

```python
find_functions_by_names(self, *function_names: tuple[str, ...]) -> ASTNodeList
```

Finds function nodes that match any of the specified function names and returns them as an ASTNodeList.

<br />

```python
find_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList
```

Finds nodes that match any of the specified identifiers within the AST and returns them as an ASTNodeList.

<br />

```python
find_method_calls(self, caller: str, method: str) -> ASTNodeList
```

Finds method call nodes where the caller matches the specified identifier and the method name matches the specified method and returns them as an ASTNodeList.

<br />

```python
find_assignments(self, ident: str, value_ident: str) -> ASTNodeList
```

Finds assignment nodes where the left-hand side matches the specified identifier and the right-hand side matches the specified value identifier and returns them as an ASTNodeList.

<br />

```python
find_mutables(self) -> ASTNodeList
```

Finds nodes marked as `mut: true` within the AST and returns them as an ASTNodeList.

<br />

```python
find_account_typed_nodes(self, ident: str) -> ASTNodeList
```

Finds nodes that are Account-typed based on their access_path and parent identifier and returns them as an ASTNodeList.

<br />

```python
find_member_accesses(self, ident: str) -> ASTNodeList
```

Finds nodes that represent member accesses matching the specified identifier within the AST and returns them as an ASTNodeList.

<br />

```python
to_raw_ast_debug(self)
```

Prints the raw AST representation of the current node (scoped to this specific node only, not the entire AST tree) in JSON format for debugging purposes and returns the node itself. This method outputs detailed AST structure including identifiers, parent relationships, and all node data to help with template development and debugging.

## ASTNodeList, ASTNodeListGroup

```python
first(self)
```

Returns the first node in the list or calls `exit_on_none` if the list is empty.

<br />

```python
to_result(self)
```

Converts each node in the list to its dictionary representation and returns the list of these representations, in a format suitable for serialization and further processing as a finding result location.

<br />

```python
exit_on_none(self)
```

Raises a StopIteration exception if the list is empty. Allows wrapping a for loop iteration within try/except, and continue to the next iteration when the return value of the previous function is None.

```python
exit_on_value(self)
```

Raises a StopIteration exception if the list contains any nodes. Allows wrapping a for loop iteration within try/except, and continue to the next iteration when the return value of the previous function has results.

<br />

```python
to_raw_ast_debug(self)
```

Prints the raw AST representation of all nodes in the list/group (scoped to only these specific nodes, not the entire AST tree) in JSON format for debugging purposes and returns the list/group itself. For ASTNodeList, it outputs each node's data. For ASTNodeListGroup, it outputs grouped node data. This method is useful for template development and debugging to understand the specific AST structure of the current scope.
