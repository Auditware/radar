# Template Writing Guide

Templates are YAML files that define security checks for smart contracts. Each template operates on AST nodes and uses a DSL to query and identify vulnerable patterns.

## Template Structure

```yaml
version: 0.1.0
author: your-name
accent: anchor  # or stylus, solidity
name: Template Name
description: Brief description of the vulnerability
severity: Low|Medium|High
certainty: Low|Medium|High
vulnerable_example: URL to example vulnerable code
rule: |
  for source, nodes in ast:
      try:
          # Your detection logic here
      except:
          continue
```

## Core Principles

### Zero False Positives
Templates MUST NOT produce false positives. Every detection must be a real issue.

### Generalize Patterns
Write rules that generalize from specific examples to catch similar issues across contracts. Don't hard-code values or make rules contract-specific.

### Keep It Simple
Avoid complex logic that's hard to maintain. Prefer clear, readable code over clever tricks.

### Point to the Core Issue
Results must point to the exact line that represents the vulnerability, not just the function or file.

## Template Rule Flow

Rules operate on `(source, nodes)` pairs from the AST iterator:
- `source`: File path
- `nodes`: RustASTNode with DSL methods for querying

Common pattern:
```python
for source, nodes in ast:
    try:
        # Find patterns
        vulnerable_pattern = nodes.find_by_names("SomeType").exit_on_none()
        
        # Verify absence of mitigation
        nodes.find_by_names("SafeguardType").exit_on_value()
        
        # Report the issue
        print(vulnerable_pattern.first().to_result())
    except:
        continue
```

## Essential DSL Methods

### Exit Controls
- `exit_on_none()`: Stop if no matches (pattern not found)
- `exit_on_value()`: Stop if matches found (safeguard exists)

These prevent exceptions and control rule flow efficiently.

### Finding Patterns
- `find_by_names(*idents)`: Find nodes by identifier
- `find_functions_by_names(*names)`: Find function declarations
- `find_method_calls(caller, method)`: Find method invocations
- `find_chained_calls(*idents)`: Find chained method calls
- `find_comparison_involving(ident)`: Find comparisons with identifier
- `find_macro_attribute_by_names(*idents)`: Find macro attributes

### Accessing Results
- `first()`: Get first node from list
- `to_result()`: Convert to structured finding format
- `to_raw_ast_debug()`: Debug AST structure (don't call print, just add to code)

## Writing Workflow

1. **Understand the vulnerability**: Study real examples
2. **Identify the pattern**: What makes code vulnerable?
3. **Identify mitigations**: What makes code safe?
4. **Write the rule**: Detect pattern, verify no mitigation
5. **Test against bad example**: Must detect all issues
6. **Test against good example**: Must detect nothing
7. **Add unit test**: Add to `api/tests/test_templates.py`

## Testing

Every template requires:
- `api/tests/mocks/<template_name>/bad/src/lib.rs`: Vulnerable code
- `api/tests/mocks/<template_name>/good/src/lib.rs`: Safe code
- Unit test in `api/tests/test_templates.py`

Test with:
```bash
radar --dev --path api/tests/mocks/<template_name>/bad --ast --output outputs/out.json
```

Use `--ast` flag to inspect AST structure and verify your rule logic.

## Common Patterns

### Pattern: Missing check
```python
# Detect usage of risky pattern
risky = nodes.find_by_names("RiskyType").exit_on_none()

# Verify no safeguard
nodes.find_by_names("SafeguardType").exit_on_value()

# Report
print(risky.first().to_result())
```

### Pattern: Incorrect ordering
```python
# Find state changes
state_change = nodes.find_by_names("state_var").exit_on_none()

# Find external calls
external_call = nodes.find_method_calls("ctx", "invoke").exit_on_none()

# Report if state change happens after call (simplified)
print(state_change.first().to_result())
```

## Debugging

1. Use `--dev` mode for detailed logs
2. Add `node.to_raw_ast_debug()` in template to inspect AST
3. Check `dsl_log` decorator output for function call traces
4. Test one template at a time against one contract
5. Run `make test` before considering feature complete

## Avoid

- Comments unless absolutely necessary
- Hard-coded values or contract-specific logic
- Overly complex queries
- Generic detections (e.g., all imports)
- False positives (0% tolerance)
