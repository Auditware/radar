---
name: radar
description: Use radar for multi-framework smart contract AST generation and security analysis. Supports Rust (Anchor, native, Stylus) and Solidity (standard, Foundry). Triggers include generating AST, finding vulnerabilities, debugging via AST output, writing security templates, contributing detection rules, or working with radar's template DSL. Use when users mention radar, AST generation for Rust/Solidity/Anchor/Stylus/Foundry, smart contract parsing, vulnerability detection, template development, or security scanning.
---

# radar

Radar is a multi-framework AST generator and security analysis tool for smart contracts. Use this skill for AST generation across Rust and Solidity ecosystems, smart contract vulnerability scanning, and radar template development to repeat detection patterns to be reused against multiple contracts.

## Supported Frameworks

- **Anchor** (Solana framework)
- **Native Rust** (Solana programs)  
- **Stylus** (Arbitrum Rust)
- **Solidity** (standalone contracts)
- **Foundry** (Solidity projects)

All use Rust's `syn` parser for consistent, high-quality AST output.

## Generating AST

### AST for Any Framework
```bash
radar -p <contract-path> --ast -o output.json
```

Output includes both security findings and complete AST structure.

### AST-Only Mode
Generate AST without security scanning:
```bash
radar -p <contract-path> --ast --ignore low,medium,high,uncertain -o ast.json
```

### Framework Examples
```bash
# Anchor project
radar -p ./my-anchor-project --ast -o anchor_ast.json

# Native Rust (Solana)
radar -p ./native-solana --ast -o rust_ast.json

# Stylus (Arbitrum)
radar -p ./stylus-contract --ast -o stylus_ast.json

# Solidity
radar -p ./solidity-contract --ast -o solidity_ast.json

# Foundry project
radar -p ./foundry-project --ast -o foundry_ast.json
```

See [ast-generation.md](references/ast-generation.md) for complete AST guide including structure, node types, and integration patterns.

## Running Scans

### Basic Scan
```bash
radar -p <contract-path>
```

### With AST Output
Essential for template development and debugging:
```bash
radar --dev -p <contract-path> --ast -o output.json
```

### Custom Templates
```bash
radar -p <contract-path> -t <templates-directory>
```

See [usage.md](references/usage.md) for complete command reference and integration options.

## Developing Templates

Templates are YAML files that detect vulnerable patterns using a Python DSL.

### Quick Template Structure
```yaml
version: 0.1.0
author: your-name
accent: anchor
name: Template Name
description: Vulnerability description
severity: Low|Medium|High
certainty: Low|Medium|High
vulnerable_example: URL
rule: |
  for source, nodes in ast:
      try:
          pattern = nodes.find_by_names("VulnType").exit_on_none()
          nodes.find_by_names("Safeguard").exit_on_value()
          print(pattern.first().to_result())
      except:
          continue
```

### Development Workflow
1. Run radar with `--ast` to inspect contract structure
2. Write rule using DSL functions to detect vulnerable patterns
3. Test against bad example (must detect)
4. Test against good example (must not detect)
5. Add unit test to `api/tests/test_templates.py`
6. Run `make test`

### Key Rules
- Zero false positives (absolute requirement)
- Point to exact vulnerability line, not function/file
- Generalize patterns, don't hard-code values
- Use `exit_on_none()` when pattern must exist
- Use `exit_on_value()` to verify safeguard absence

See [template-writing.md](references/template-writing.md) for complete guide.

## DSL Functions

Template rules use methods from `RustASTNode`:

### Finding Patterns
- `find_by_names(*idents)` - Find by identifier
- `find_functions_by_names(*names)` - Find function declarations
- `find_method_calls(caller, method)` - Find method invocations
- `find_chained_calls(*idents)` - Find chained calls
- `find_comparison_involving(ident)` - Find comparisons
- `find_macro_attribute_by_names(*idents)` - Find macro attributes

### Control Flow
- `exit_on_none()` - Stop if not found (pattern required)
- `exit_on_value()` - Stop if found (safeguard exists)
- `first()` - Get first node
- `to_result()` - Convert to finding format

### Debugging
- `to_raw_ast_debug()` - Inspect AST structure (add to template, don't call print)

See [dsl-functions.md](references/dsl-functions.md) for complete API reference.

## Testing Templates

Every template requires:
- `api/tests/mocks/<template_name>/bad/src/lib.rs` - Vulnerable code
- `api/tests/mocks/<template_name>/good/src/lib.rs` - Safe code  
- Unit test in `api/tests/test_templates.py`

Test command:
```bash
radar --dev -p api/tests/mocks/<template_name>/bad --ast -o outputs/out.json
```

## Debugging

### Template Not Detecting
1. Run with `--dev` for detailed logs
2. Add `nodes.to_raw_ast_debug()` in template to inspect AST
3. Compare AST structure with template logic
4. Verify DSL methods exist on node type

### False Positives
Review template logic - templates must have 0% false positive rate.

### AST Inspection
Use `--ast` flag to understand contract structure:
```bash
radar --dev -p <contract> --ast -o debug.json
```

Examine the `ast` field in output to see node structure.

## Contributing

Templates are the primary contribution method. Each template must:
- Detect a real vulnerability pattern
- Have zero false positives
- Include bad/good test cases
- Pass unit tests

See [template-writing.md](references/template-writing.md) for complete contribution guide.
