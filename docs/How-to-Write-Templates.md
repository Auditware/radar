# radar Templates

## Template example

```yaml
version: 0.1.0
author: forefy
name: Arbitrary Cross-Program Invocation
severity: Medium
certainty: Medium
description: If not validated properly, when a program implements a Cross-Program Invocation, callers of the program may provide an arbitrary or untrusted program - manipulating the program to call instructions on an untrusted target program.
rule: |
  for source, nodes in ast:
      try:
          cpi_groups = nodes.find_chained_calls("solana_program", "program", "invoke").exit_on_none()
          nodes.find_comparisons("spl_token", "token_program").exit_on_value()
          for cpi_group in cpi_groups:
              print(cpi_group.first().parent.to_result())
      except:
          continue
```

A template consists of descriptive fields, and a logical rule.

The descriptive fields represent the information associated with the vulnerability and the template itself.

The rule is python based statements through which we iterate on the AST (Abstract Syntax Tree) of the contract and extract insightful information.

## Understanding Rules

At a first glance, we can see that we have the `ast` variable magically available to us, and that we can iterate on it in `source` and `nodes` pairs.

`source` is the file path of the current iteration

`nodes` are the nodes of that specific file path

Then we have the real magic, demonstrated on line 3 of the rule above:
```python
cpi_groups = nodes.find_chained_calls("solana_program", "program", "invoke").exit_on_none()
``` 

We have setup ease-of-use functions, and there are operations that can be done on each.

These functions live in a single file in the repo [dsl_ast_iterator.py](https://github.com/Auditware/radar/blob/main/api/utils/dsl/dsl_ast_iterator.py), and to deep dive and understand the different methods available that's the place to be.

In a high level, there are three important classes: `ASTNode`, `ASTNodeList` and `ASTNodeListGroup`, all give us an abstraction to iterate over the rust JSON AST radar generates.

`ASTNode` represent an AST node, and the layers above it (List, ListGroup) can be thought of similarly - the functions implemented on `ASTNode` can be called in the Node, List, or ListGroup level accordingly.

In the code snippet above we iterate on an `ASTNodeList`, retreiving occurrences of `solana_program::program::invoke(..)`.

That returns us List Groups (i.e. list of ast node lists) of the nodes involved in those occurrences, including further relevant data like line positioning, metadata, child nodes, parent nodes etc.

We can then use this info and pass it to more methods, filtering results further, or print nodes based on conditions we choose.

When we want to indicate a result, we just print the vulnerable node found (or the node whose line information we want to include in the raised vulnerability/insight):

```python
for cpi_group in cpi_groups:
    print(cpi_group.first().parent.to_result())
```

In that example we printed the first CPI's parent from each node list group, using the `.to_result()` to ensure it's picked up as a vulnerability item.

For an easy learning curve, we've setup [demo.ipynb](https://github.com/Auditware/radar/blob/main/demo.ipynb) in which you can start playing with a simulated rule and see results, no docker setup needed!