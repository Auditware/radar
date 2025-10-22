# Copilot Instructions for Radar

## Core details
- radar is a cli tool running mostly locally via docker-compose or as a CI job via `radar-action`.
- `/api/` container is a django REST API processing the rust (via rust_syn_wrapper) and running python queries from user-defined templates.
- `/controller/` container is an orchestrator bridging between user filesystem and the api container, handling CLI args, file mounting, and result formatting.
- `/api/rust_syn_wrapper/` is being compiled to the api container as a shared library, providing python bindings to rust's syn parser for AST generation.
- `radar -p <contract-path>` runs the analysis on the specified smart contract path.
- to run in dev mode (building from local source), use `radar -d -p <contract-path>`.
- if you debug templates or write new ones, use `radar -d -p <contract-path> -a -o out.json`, this will help you inspect ast, results, and compare them to the template code to provide quality results.

## Radar templates
Templates are YAML files defining security checks to be made:

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

When writing or changing templates, ensure to refer to the following documentation for guidance:
- https://github.com/auditware/radar/wiki/How-to-Write-Templates
- https://github.com/auditware/radar/wiki/Rule-Functions

When radar writing templates, strictly avoid:
- Writing templates that tend to produce false positives.
- Writing templates that are too generic and match many benign patterns.
- Writing templates that are too specific and miss relevant patterns.
- Using complex logic that is hard to maintain or understand.
- Using inefficient queries that slow down the analysis significantly.