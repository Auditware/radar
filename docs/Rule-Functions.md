# Rule Functions Documentation

Here you can read descriptions about the core instance methods used by the abstraction functionality of the radar template rule syntax. See [How to write templates](https://github.com/Auditware/radar/wiki/How-to-Write-Templates)

## ASTNode

```python
to_result(self)
```

Converts the current node and its children into a dictionary format suitable for serialization and further processing as a finding result location.

---

```python
find_by_parent(self, parent_ident: str) -> ASTNodeList
```

Finds all nodes whose parent has the specified identifier and returns them as an ASTNodeList.

---

```python
find_chained_calls(self, *idents: tuple[str, ...]) -> ASTNodeListGroup
```

Finds sequences of sequential nodes matching the specified identifiers and returns them as an ASTNodeListGroup.

---

```python
find_by_access_path(self, access_path: str, keyword: str) -> ASTNodeList
```

Finds nodes whose access_path contains the specified keyword within the specified access path and returns them as an ASTNodeList.

`access_path` is a value representing the sequence of AST nodes walked until indexing of the node, that did not get indexed (due to not being a prime node).

---

```python
find_comparisons(self, ident1: str, ident2: str)
```

Finds binary comparisons between the specified identifiers within the AST and returns them as an ASTNodeList.

---

```python
find_comparison_to_any(self, ident: str)
```

Finds any node involved in a comparison with the specified identifier and returns them as an ASTNodeList.

---

```python
find_negative_of_operation(self, operation_name: str, *args: tuple) -> ASTNodeList
```

Finds nodes that do not match the results of the specified operation and returns them as an ASTNodeList.

"operation" refers to an ASTNode instance method.

---

```python
find_functions_by_names(self, *function_names: tuple[str, ...]) -> ASTNodeList
```

Finds function nodes that match any of the specified function names and returns them as an ASTNodeList.

---

```python
find_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList
```

Finds nodes that match any of the specified identifiers within the AST and returns them as an ASTNodeList.

---

```python
find_method_calls(self, caller: str, method: str) -> ASTNodeList
```

Finds method call nodes where the caller matches the specified identifier and the method name matches the specified method and returns them as an ASTNodeList.

---

```python
find_assignments(self, ident: str, value_ident: str) -> ASTNodeList
```

Finds assignment nodes where the left-hand side matches the specified identifier and the right-hand side matches the specified value identifier and returns them as an ASTNodeList.

---

```python
find_mutables(self) -> ASTNodeList
```

Finds nodes marked as `mut: true` within the AST and returns them as an ASTNodeList.

---

```python
find_account_typed_nodes(self, ident: str) -> ASTNodeList
```

Finds nodes that are Account-typed based on their access_path and parent identifier and returns them as an ASTNodeList.

---

```python
find_member_accesses(self, ident: str) -> ASTNodeList
```

Finds nodes that represent member accesses matching the specified identifier within the AST and returns them as an ASTNodeList.

## ASTNodeList, ASTNodeListGroup

```python
first(self)
```

Returns the first node in the list or calls `exit_on_none` if the list is empty.

---

```python
to_result(self)
```

Converts each node in the list to its dictionary representation and returns the list of these representations, in a format suitable for serialization and further processing as a finding result location.

---

```python
exit_on_none(self)
```

Raises a StopIteration exception if the list is empty. Allows wrapping a for loop iteration within try/except, and continue to the next iteration when the return value of the previous function is None.

```python
exit_on_value(self)
```

Raises a StopIteration exception if the list contains any nodes. Allows wrapping a for loop iteration within try/except, and continue to the next iteration when the return value of the previous function has results.
