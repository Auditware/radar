# DSL Function Reference

Template rules inherit from `RustASTNode` in `api/utils/dsl/dsl_ast_iterator.py`. These methods enable querying and navigating the AST.

## Control Flow

### exit_on_none()
Stop execution if no nodes are found. Use when a pattern must exist.

```python
nodes.find_by_names("Signer").exit_on_none()  # Stop if no Signer found
```

### exit_on_value()
Stop execution if nodes are found. Use to verify absence of a safeguard.

```python
nodes.find_by_names("Signer").exit_on_value()  # Stop if Signer exists
```

## Finding Patterns

### find_by_names(*idents)
Find nodes by identifier name.

```python
nodes.find_by_names("Account", "Signer")  # Find Account or Signer
```

### find_functions_by_names(*function_names)
Find function declarations by name.

```python
nodes.find_functions_by_names("initialize", "update")
```

### find_all_functions()
Find all function declarations.

```python
all_funcs = nodes.find_all_functions()
```

### find_method_calls(caller, method)
Find method invocations on a specific caller.

```python
nodes.find_method_calls("ctx", "invoke")  # Find ctx.invoke() calls
```

### find_chained_calls(*idents)
Find chained method calls in sequence.

```python
nodes.find_chained_calls("derive", "Accounts")  # Find .derive().Accounts()
```

### find_macro_attribute_by_names(*idents)
Find macro attributes by name.

```python
nodes.find_macro_attribute_by_names("program", "account")
```

### find_comparison_involving(ident)
Find comparison operations involving an identifier.

```python
nodes.find_comparison_involving("is_signer")  # Find comparisons with is_signer
```

### find_comparisons_between(ident1, ident2)
Find comparisons between two identifiers.

```python
nodes.find_comparisons_between("balance", "amount")
```

### find_member_accesses(member)
Find member access operations.

```python
nodes.find_member_accesses("is_signer")  # Find .is_signer accesses
```

### find_by_access_path(access_path_part)
Find nodes by access path substring.

```python
nodes.find_by_access_path("accounts.user")
```

### find_by_similar_access_path(access_path_part)
Find nodes with similar access paths (fuzzy matching).

```python
nodes.find_by_similar_access_path("ctx.accounts")
```

### find_by_parent(parent_ident)
Find nodes with a specific parent identifier.

```python
nodes.find_by_parent("MyStruct")
```

### find_by_child(child_ident)
Find nodes containing a specific child identifier.

```python
nodes.find_by_child("inner_field")
```

### find_negative_of_operation(operation_type)
Find logical negations of specific operations.

```python
nodes.find_negative_of_operation("comparison")
```

## Result Manipulation

### first()
Get the first node from a list. Raises StopIteration if empty.

```python
vulnerable_node = nodes.find_by_names("RiskyType").first()
```

### to_result()
Convert node to structured finding format for radar output.

```python
print(vulnerable_node.to_result())  # Report the issue
```

### to_raw_ast_debug()
Print detailed AST structure for debugging. Don't call print(), just add to template code.

```python
some_nodes.to_raw_ast_debug()  # Debug helper
```

## Node Lists

Methods return `ASTNodeList` or `ASTNodeListGroup` which support:
- Iteration: `for node in node_list:`
- Indexing: `node_list[0]`
- Length: `len(node_list)`
- Chaining: All methods return lists for further querying

## Common Combinations

### Detect pattern without safeguard
```python
risky = nodes.find_by_names("UnsafeType").exit_on_none()
nodes.find_comparison_involving("is_safe").exit_on_value()
print(risky.first().to_result())
```

### Find function with missing check
```python
func = nodes.find_functions_by_names("transfer").exit_on_none()
func.find_by_names("Signer").exit_on_value()
print(func.first().to_result())
```

### Chain multiple queries
```python
accounts = nodes.find_macro_attribute_by_names("account").exit_on_none()
missing_check = accounts.find_by_names("Signer").exit_on_none()
print(missing_check.first().to_result())
```

## Error Handling

All template rules run in try/except blocks:
```python
for source, nodes in ast:
    try:
        # Rule logic
    except:
        continue  # Skip this file on any error
```

Use `exit_on_none()` and `exit_on_value()` to control flow instead of manual exception handling.
