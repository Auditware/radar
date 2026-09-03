# DSL notes

Full Rust reference: `docs/Rule-Functions.md` (published to the wiki). This file covers what that reference does not: the Solidity method set, the idioms the corpus actually uses, and three signatures that are easy to get wrong.

## Rule shape

`ast` is injected as `dict.items()`; `nodes` is the root node for one file - a `RustASTNode` or `SolidityASTNode` depending on the template's `language`. Nothing inherits anything; the rule is a script.

```python
for source, nodes in ast:
    try:
        for function in nodes.find_all_functions():
            hits = function.find_chained_calls("unpack")
            if not hits:
                continue
            if function.find_comparison_involving("owner").nodes:
                continue          # guarded, not vulnerable
            for hit in hits:
                print(hit.to_result())
    except:
        continue
```

A finding is reported by `print()`ing a node's `to_result()`. Anything printed that is not a valid node lands in the finding's `debug` field instead.

Two styles coexist. Explicit iteration with `.nodes` truthiness (above) is the majority and is easier to reason about. The `exit_on_none()` / `exit_on_value()` style raises `StopIteration` to abort the file - compact, but it shares the bare `except` with real errors, so a typo reads as "pattern absent".

## Signatures worth checking

| Call | Note |
|---|---|
| `find_by_similar_access_path(access_path, stop_keyword)` | **Two** required arguments - the path, and the keyword it is truncated at |
| `find_negative_of_operation(operation_name, *args)` | `operation_name` is another ASTNode **method name**, looked up with `getattr` and called with `*args`, e.g. `("find_comparisons_between", "a", "b")` |
| `find_chained_calls(*idents)` | Matches **consecutive sibling children** whose idents equal the arguments in order, returning an `ASTNodeListGroup`. Not method chaining |

## RustASTNode

```
find_by_names(*idents)                find_all_functions()
find_functions_by_names(*names)       find_method_calls(caller, method)
find_chained_calls(*idents)           find_macro_attribute_by_names(*idents)
find_by_parent(parent_ident)          find_by_child(child_ident)
find_by_access_path(part)             find_by_similar_access_path(path, stop_keyword)
find_comparison_involving(ident)      find_comparisons_between(ident1, ident2)
find_member_accesses(ident)           find_binary_operations(*operators)
find_assignments(ident, value_ident)  find_mutables()
find_account_typed_nodes(ident)       find_negative_of_operation(op_name, *args)
```

## SolidityASTNode

A different class (`api/utils/dsl/solidity.py`) with a different set. The Rust methods above are **not** available on it.

```
find_all_functions()                    find_nodes_by_names(*names)
find_nodes_by_types(*types)             find_nodes_by_member_names(*names)
find_nodes_by_operators(*operators)     find_nodes_by_metadata_key(key, *patterns)
find_nodes_by_type_strings(*patterns)   find_nodes_by_type_identifiers(*patterns)
find_modifiers_by_names(*names)         find_functions_by_name_patterns(*patterns)
find_external_calls()                   find_setters_and_constructors()
find_functions_with_address_assignments()
find_similar_function_definitions()
find_comparisons_between(*names)
```

## On every result list

`first()`, `to_result()`, `to_raw_ast_debug()`, `exit_on_none()`, `exit_on_value()`, plus `.nodes`, iteration, indexing and `len()`. `first()` on an empty list raises `StopIteration`, same as `exit_on_none()`.

## Sandbox

Allowed builtins: `print len range dict list tuple set type`. No imports. Everything else - `any`, `all`, `sorted`, `enumerate`, `str`, `int`, `isinstance`, `min`, `max`, `sum` - raises `RuntimeError`, which the rule's `except` swallows. Methods on objects are fine: `.startswith()`, `.split()`, `.lower()`, `.get()` are used throughout the corpus.
