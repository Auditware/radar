# Contribution guidelines
- Follow the existing coding style and conventions
- Avoid adding comments to the code that are not absolutely necessary
- Avoid emojis in the code
- Read radar templates rules section in this file before making template changes - AN ABSOLUTE MUST

# Core details
- radar is a cli tool running mostly locally via docker-compose or as a CI job via `radar-action`
- radar is an open source tool available at https://github.com/Auditware/radar
- `/api/` container is a django REST API processing the rust (via rust_syn_wrapper) and running python queries from user-defined templates
- `/controller/` container is an orchestrator bridging between user filesystem and the api container, handling CLI args, file mounting, and result formatting
- `/api/rust_syn_wrapper/` is being compiled to the api container as a shared library, providing python bindings to rust's syn parser for AST generation
- radar templates are YAML files defining security checks to be made by the radar engine. existing ones are in `/api/builtin_templates/`
- radar templates are written in a DSL defined in `/api/utils/dsl/`
- radar template rules operate on AST nodes provided by rust's syn parser via rust_syn_wrapper
- radar template rules inherit from a base set of functions defined in `/api/utils/dsl/dsl_ast_iterator.py`
- radar template rule indicate a found issue by calling `print()` on a node (the node or nodes list that represent the issue and should be marked as the core problem), and specifically `print(node.to_result())` to get structured output that radar can parse into a structured finding
- `radar -p <contract-path>` runs the analysis on the specified smart contract path
- to run in dev mode (building from local source), use `radar -d -p <contract-path>`

# radar templates rules
- Refer to these resources:
  - https://github.com/auditware/radar/wiki/Rule-Functions
  - https://github.com/auditware/radar/wiki/How-to-Write-Templates
- Use `./radar --dev --path <contract-path> --ast --output outputs/out.json`, this will help you inspect ast, results, and compare them to the template code to provide quality results
- Do not write temporary template files for debug, use the template you are working on directly§
- Place temporary print statements within the template you are working on to make line-by-line sense of the rule behavior
- Template rules may not produce false positives (0 false positive rate - AN ABSOLUTE MUST)
- Strive for the highest detection rates of true positives
- Template rules may not be too generic / match benign patterns / use hard-coded values or non-deterministic behavior
- Some rules may introduce complexities that are not solvable on the rule level, in such cases, try to resolve on this order:
  - Find a workaround on the template code level
  - See if adding a utility function to `api/utils/dsl/dsl_ast_iterator.py` helps significantly
  - In rare cases, investigate for a core issue on `api/utils/ast.py`
- Avoid using complex logic that is hard to maintain or understand
- Avoid using inefficient queries that slow down the analysis significantly
- Avoid adding comments to template code
- Try to have a consistent code and description writing style across templates
- Try to strive for a shorter yet readable template rule code