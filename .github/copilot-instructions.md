# Copilot Instructions for Radar

## Project Overview

Radar is a static analysis tool for Anchor Rust programs designed to identify security vulnerabilities in Solana smart contracts. It uses a Python-based rule engine with YAML templates to detect vulnerable code patterns through logical expressions.

## Architecture

### Core Components

1. **API Service** (`/api/`) - Django-based backend that:
   - Processes Rust source code using AST analysis
   - Executes security rule templates against parsed code
   - Manages scan results and template storage
   - Provides REST endpoints for the controller

2. **Controller Service** (`/controller/`) - Python orchestrator that:
   - Handles CLI arguments and file operations
   - Coordinates between host filesystem and containerized API
   - Manages Docker volume mounting for file access
   - Formats and outputs scan results

3. **rust_syn_wrapper** (`/api/rust_syn_wrapper/`) - Rust library that:
   - Provides Python bindings for Rust's `syn` parser
   - Converts Rust source code to JSON AST representation
   - Built as a shared library (`librust_syn.so`) during Docker build
   - Imported as `rust_syn` module in Python code

### Key Technologies

- **Backend**: Django REST Framework with Celery for async processing
- **Database**: PostgreSQL for persistence
- **Message Queue**: RabbitMQ for Celery task distribution
- **AST Parsing**: Rust `syn` crate with Python bindings via PyO3
- **Containerization**: Docker with multi-stage builds

## Running the Project

### 1. Production Mode (GHCR Images)

Uses pre-built images from GitHub Container Registry:

```bash
# Uses docker-compose.yml
./radar -p <contract-path>
```

**Key characteristics:**
- Images: `ghcr.io/auditware/radar-api:main` and `ghcr.io/auditware/radar-controller:main`
- Fast startup - no local building required
- Suitable for CI/CD and general usage

### 2. Development Mode (Local Build)

Builds containers from local source code:

```bash
# Uses docker-compose-dev.yml
./radar --dev -p <contract-path>
```

**Key characteristics:**
- Builds from local `Dockerfile`s in `api/` and `controller/` directories
- Includes Rust compilation step for `rust_syn_wrapper`
- Slower startup but reflects local code changes
- Essential for development and testing

## Security Rule Templates

Templates are YAML files defining security checks:

```yaml
version: 0.1.0
author: <author>
name: <rule-name>
severity: <Low|Medium|High>
certainty: <Low|Medium|High>
description: <description>
rule: |
  # Python code using DSL for AST analysis
  for source, nodes in ast:
      # Template logic here
```

### Template Locations
- **Built-in**: `/api/builtin_templates/` - Shipped with radar
- **Custom**: Any directory specified with `-t <templates_directory>`

### DSL Functions
The rule engine provides a domain-specific language for AST traversal:
- `nodes.find_chained_calls()` - Find method call chains
- `nodes.find_by_names()` - Find nodes by identifier names
- `nodes.find_comparisons()` - Find comparison expressions
- `nodes.find_member_accesses()` - Find field/member access

## Development Guidelines

### Working with rust_syn_wrapper

When modifying the Rust AST parser:

1. **Location**: `/api/rust_syn_wrapper/src/lib.rs`
2. **Purpose**: Converts Rust code to JSON AST via `syn` crate
3. **Build Process**: Compiled during Docker build in multi-stage process
4. **Usage**: Imported as `rust_syn` Python module in `/api/utils/ast.py`

**Key points:**
- PyO3 provides Python bindings
- Must rebuild Docker images when changed
- Output is JSON-serialized AST from `syn` crate

### File Structure Conventions

- **Templates**: YAML files with specific schema
- **AST Processing**: `/api/utils/ast.py` handles Rust code parsing
- **DSL Engine**: `/api/utils/dsl/` contains rule execution sandbox
- **Tests**: Mock AST data in `/api/tests/mocks/` for testing

### Docker Development

- **Development**: Use `docker-compose-dev.yml` for local builds
- **Production**: Use `docker-compose.yml` for GHCR images
- **Volumes**: `radar_data` volume enables file sharing between containers
- **Health Checks**: API service includes readiness probes

### Testing

- **Test Projects**: `/api/tests/mocks/anchor-test/` contains sample Anchor projects
- **Mock Data**: Pre-generated AST JSON for consistent testing
- **Rule Testing**: Templates can be tested against mock contract code

## Code Style and Patterns

### Python Code
- Follow Django conventions for API service
- Use type hints where possible
- Sandbox rule execution for security
- Handle AST parsing errors gracefully

### Rust Code
- Keep `rust_syn_wrapper` minimal and focused
- Use `syn` crate's full feature set for comprehensive parsing
- Return JSON-serialized AST for Python consumption

### YAML Templates
- Include comprehensive metadata (author, severity, description)
- Write clear, readable rule logic
- Handle edge cases with try/except blocks
- Use descriptive variable names in DSL code

## Security Considerations

- Rule templates execute in sandboxed environment
- Limited builtins and imports available in DSL
- AST analysis is read-only - no code modification
- Container isolation prevents host system access

## Common Development Tasks

1. **Adding New Templates**: Create YAML file in `/api/builtin_templates/`
2. **Extending DSL**: Modify functions in `/api/utils/dsl/dsl_ast_iterator.py`
3. **Updating AST Parser**: Edit `/api/rust_syn_wrapper/src/lib.rs` and rebuild
4. **Testing Changes**: Use `--dev` flag to build from local source
