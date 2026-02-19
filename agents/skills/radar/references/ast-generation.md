# AST Generation Guide

Radar generates Abstract Syntax Trees (ASTs) for multiple smart contract languages and frameworks. Many users leverage radar purely for its AST generation capabilities, independent of security scanning.

## Supported Languages & Frameworks

### Rust-Based
- **Anchor** (Solana framework)
- **Native Rust** (Solana programs)
- **Stylus** (Arbitrum Rust contracts)

### Solidity-Based
- **Solidity** (standalone contracts)
- **Foundry** (Solidity projects)

All frameworks use Rust's `syn` parser via `rust_syn_wrapper` for consistent, high-quality AST output.

## Generating AST Output

### Basic AST Generation
```bash
radar -p <contract-path> --ast -o output.json
```

This produces a JSON file with two main sections:
- `results`: Security findings (empty if no issues)
- `ast`: Complete AST structure of all scanned files

### AST-Only Mode
To generate AST without running security scans, use a minimal template directory or ignore all severities:

```bash
# Option 1: Ignore all severities
radar -p <contract-path> --ast --ignore low,medium,high,uncertain -o output.json

# Option 2: Empty template directory
mkdir empty_templates
radar -p <contract-path> --ast -t empty_templates -o output.json
```

## Framework-Specific Examples

### Anchor Projects
```bash
radar -p ./my-anchor-project --ast -o anchor_ast.json
```

Detects Anchor macros (`#[program]`, `#[account]`, etc.) and generates AST including:
- Account structures
- Program instructions
- Context definitions
- CPI calls

### Native Rust (Solana)
```bash
radar -p ./native-solana-program --ast -o rust_ast.json
```

Parses raw Solana programs without Anchor framework.

### Stylus Contracts
```bash
radar -p ./stylus-contract --ast -o stylus_ast.json
```

Generates AST for Arbitrum Stylus Rust contracts.

### Solidity Contracts
```bash
radar -p ./solidity-contract --ast -o solidity_ast.json
```

Parses standalone Solidity files.

### Foundry Projects
```bash
radar -p ./foundry-project --ast -o foundry_ast.json
```

Scans entire Foundry project structure including:
- Source contracts (`src/`)
- Test contracts (`test/`)
- Scripts (`script/`)
- Libraries (`lib/`)

## AST Structure

The output JSON has this structure:

```json
{
  "results": [...],
  "ast": {
    "file1.rs": {
      "nodes": [
        {
          "type": "ItemFn",
          "ident": "function_name",
          "access_path": "root.function_name",
          "children": [...],
          "metadata": {...}
        }
      ]
    },
    "file2.rs": {...}
  }
}
```

### Key AST Fields
- `type`: Node type (ItemFn, ItemStruct, Expr, etc.)
- `ident`: Identifier/name of the node
- `access_path`: Hierarchical path to the node
- `children`: Nested child nodes
- `metadata`: Additional context (line numbers, attributes, etc.)

## Using AST for Development

### Understanding Contract Structure
```bash
# Generate AST
radar --dev -p <contract-path> --ast -o debug.json

# Open debug.json and examine:
# - Function declarations (ItemFn)
# - Struct definitions (ItemStruct)
# - Macro attributes (Attribute)
# - Method calls (MethodCall)
# - Comparisons (ExprBinary)
```

### Template Development Workflow
1. **Generate AST of vulnerable contract**:
   ```bash
   radar --dev -p api/tests/mocks/my_vuln/bad --ast -o bad_ast.json
   ```

2. **Examine AST structure**: Find the nodes representing the vulnerability

3. **Generate AST of safe contract**:
   ```bash
   radar --dev -p api/tests/mocks/my_vuln/good --ast -o good_ast.json
   ```

4. **Compare**: Identify what differs between vulnerable and safe patterns

5. **Write template rule**: Use DSL to query the pattern identified in the AST

### Debugging Templates
When a template doesn't work:

1. **Add debug output in template**:
   ```python
   # In your template rule
   some_nodes.to_raw_ast_debug()  # Prints AST at this point
   ```

2. **Run with AST**:
   ```bash
   radar --dev -p <contract> --ast -o debug.json
   ```

3. **Compare**: Check what the template sees vs. what's actually in the AST

## AST Node Types

Common node types you'll encounter:

### Rust/Anchor
- `ItemFn`: Function declarations
- `ItemStruct`: Struct definitions
- `ItemImpl`: Implementation blocks
- `Expr`: Expressions
- `ExprBinary`: Binary operations (comparisons, arithmetic)
- `ExprMethodCall`: Method calls (e.g., `ctx.invoke()`)
- `ExprField`: Field access (e.g., `account.is_signer`)
- `Attribute`: Macro attributes (e.g., `#[program]`)
- `Pat`: Patterns (in match, let statements)
- `Stmt`: Statements

### Solidity
Solidity ASTs follow similar patterns with contract-specific nodes for:
- Contract declarations
- Function visibility
- State variables
- Events and modifiers

## Advanced AST Usage

### Filtering Specific Files
Use the `-s/--source` flag to scope AST generation:

```bash
# Only process src/ directory
radar -p ./project --source src --ast -o src_ast.json

# Specific file
radar -p ./project --source src/lib.rs --ast -o lib_ast.json
```

### Development Mode
Always use `--dev` when working with AST for detailed logging:

```bash
radar --dev -p <path> --ast -o output.json
```

This enables:
- Verbose DSL function logs
- Detailed parsing information
- Error traces

### Output Format
AST is always in JSON format. Use the `.json` extension:

```bash
radar -p <path> --ast -o analysis.json  # ✅ Correct
radar -p <path> --ast -o analysis.md    # ❌ AST still JSON, results in MD
```

## Integration with Other Tools

The AST output can be consumed by:
- Custom analysis scripts
- IDE integrations
- Documentation generators
- Code visualization tools
- AI/ML models for code understanding

Example Python script to parse radar AST:

```python
import json

with open('output.json', 'r') as f:
    data = json.load(f)
    
ast = data['ast']
for file_path, file_data in ast.items():
    print(f"\n=== {file_path} ===")
    for node in file_data.get('nodes', []):
        if node.get('type') == 'ItemFn':
            print(f"  Function: {node.get('ident')}")
```

## Performance Notes

AST generation is fast and scales well:
- Small contracts: <1 second
- Medium projects: 1-5 seconds
- Large projects (Foundry with deps): 5-30 seconds

The bottleneck is usually Docker container startup, not parsing.

## Common Use Cases

### 1. Code Analysis Tools
Use radar as an AST frontend for custom analysis:
```bash
radar -p ./contract --ast --ignore low,medium,high -o ast.json
# Process ast.json with your tools
```

### 2. Documentation Generation
Extract function signatures, structs, and comments from AST.

### 3. Refactoring Tools
Understand code structure before automated refactoring.

### 4. Educational Purposes
Visualize how Rust/Solidity code is parsed and structured.

### 5. Template Development
Essential for writing radar security templates.

## Troubleshooting

### Empty AST Output
- Ensure contract compiles (radar skips unparseable files)
- Check file extensions (.rs, .sol)
- Verify Docker is running

### Missing Nodes
- Some nodes may be filtered by radar's parser
- Check raw output in dev mode
- Verify the code pattern you're looking for exists

### Large AST Files
For huge projects, consider:
- Using `--source` to scope to specific directories
- Processing files incrementally
- Filtering AST in post-processing
