# Usage Guide

## Installation

Radar requires Docker to be installed and running.

### Quick Install
```bash
curl -L https://raw.githubusercontent.com/auditware/radar/main/install-radar.sh | bash
```

### From Source
```bash
git clone https://github.com/auditware/radar.git
cd radar
bash install-radar.sh
```

## Basic Usage

### Scan a Contract
```bash
radar -p <path-to-contract>
```

Example:
```bash
radar -p ./my-contract
```

### Development Mode
Run from local source with debug output:
```bash
radar --dev -p <path-to-contract>
```

### Output AST
Generate AST alongside vulnerability results:
```bash
radar -p <path> --ast --output results.json
```

The AST output is essential for:
- Understanding contract structure
- Debugging template rules
- Developing new templates

### Custom Templates
Run with custom template directory:
```bash
radar -p <path> -t <templates-directory>
```

### Filter Results
Ignore specific severity levels:
```bash
radar -p <path> --ignore low,medium
```

### Output Formats
Control output via file extension:
```bash
radar -p <path> -o results.json   # JSON format
radar -p <path> -o results.md     # Markdown format
radar -p <path> -o results.sarif  # SARIF format
```

## Common Workflows

### Finding Vulnerabilities
```bash
# Basic scan
radar -p ./contract

# Scan with custom templates
radar -p ./contract -t ./my-templates

# Scan and save results
radar -p ./contract -o findings.json
```

### Developing Templates

1. **Run with AST output**:
```bash
radar --dev -p api/tests/mocks/my_template/bad --ast -o output.json
```

2. **Inspect AST structure**: Open `output.json` and examine the `ast` field

3. **Write rule in template**: Use DSL functions to query the AST

4. **Test the template**:
```bash
# Test against vulnerable code (should detect)
radar --dev -p api/tests/mocks/my_template/bad

# Test against safe code (should not detect)
radar --dev -p api/tests/mocks/my_template/good
```

5. **Run unit tests**:
```bash
make test
```

### Debugging Templates

When a template doesn't work as expected:

1. **Enable dev mode for detailed logs**:
```bash
radar --dev -p <contract-path>
```

2. **Add debug output in template**:
```python
# In your template rule
some_nodes.to_raw_ast_debug()  # Inspect AST at this point
```

3. **Run single template**:
```bash
# Create temp directory with only your template
mkdir temp_templates
cp api/builtin_templates/my_template.yaml temp_templates/
radar --dev -p <contract> -t temp_templates
```

4. **Check AST output**: Compare template logic with actual AST structure

## Command Reference

### Scan Commands
- `radar scan` or `radar -p <path>`: Run vulnerability scan
- `radar list-templates`: List all available templates
- `radar info`: Display template information
- `radar update`: Update radar to latest version

### Scan Options
- `-p, --path`: Target contract path (required)
- `-s, --source`: Specific source/scope within contract
- `-t, --templates`: Custom templates directory
- `-i, --ignore`: Severities to ignore (low,medium,high,uncertain)
- `-o, --output`: Results output file path
- `-a, --ast`: Output parsed AST
- `-d, --dev`: Development mode with debug output
- `-u, --update`: Pull latest Docker images before running
- `-ss, --store-sarif`: Accumulate SARIF results from previous runs

## Integration

### GitHub Action
Add to `.github/workflows/radar.yml`:
```yaml
name: Radar Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: Auditware/radar-action@v1
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/sh
if ! command -v radar >/dev/null 2>&1; then
  curl -sL https://raw.githubusercontent.com/auditware/radar/main/install-radar.sh | bash
fi
radar -p . --ignore low
```

Or with pre-commit framework in `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: run-radar
        name: Run radar Static Analysis
        entry: radar -p . --ignore low
        language: system
        stages: [commit]
        pass_filenames: false
        always_run: true
```
