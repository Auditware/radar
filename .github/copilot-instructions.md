# Contribution guidelines
- Follow the existing coding style and conventions
- Avoid adding comments to the code that are not absolutely necessary
- Avoid emojis in the code
- Read radar templates rules section in this file before making template changes - AN ABSOLUTE MUST
- Documentation is kept at (`docs/`) and updates via Makefile's `update-docs` to update the radar wiki. Keep documentation up to date on significant changes
- Successful testing is done only via creating a generic unit test, or via trying to run an existing template that uses the changed code to inspect results. don't use temporary test scripts
- run `make test` before considering a feature as done

# Core details
- radar is a cli tool running mostly locally via docker-compose or as a CI job via `radar-action`
- radar is an open source tool available at https://github.com/Auditware/radar
- `/api/` container is a django REST API processing the rust (via rust_syn_wrapper) and running python queries from user-defined templates
- `/controller/` container is an orchestrator bridging between user filesystem and the api container, handling CLI args, file mounting, and result formatting
- `/api/rust_syn_wrapper/` is being compiled to the api container as a shared library, providing python bindings to rust's syn parser for AST generation
- radar templates are YAML files defining security checks to be made by the radar engine. existing ones are in `/api/builtin_templates/`
- radar templates are written in a DSL defined in `/api/utils/dsl/`. the dsl is a sandboxed python environment with allowed_builtins and security restrictions
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
- Don't miss out on using `exit_on_none()` and `exit_on_value()` methods to avoid unnecessary errors and exceptions during rule execution
- Template rules may not produce false positives (0 false positive rate - AN ABSOLUTE MUST)
- Avoid using complex logic that is hard to maintain or understand
- Avoid using inefficient queries that slow down the analysis significantly
- Avoid adding comments to template code
- Try to have a consistent code and description writing style across templates
- Try to strive for a shorter yet readable template rule code
- When modifying `dsl_ast_iterator.py`, functions, try even harder to follow existing coding style and conventions
- Rules should not be made for a single specific contract, they should learn from a vulnerable pattern and generalize it to catch similar issues in other contracts reliably

## debugging radar template rules
- DO NOT write temporary files or templates for debug, use the template you are working on directly
- You can place temporary print statements within the template you are working on to make line-by-line sense of the rule behavior, but this should be very slight as the system provides relevant debugging on `dsl_log` decorator
- When debugging templates, instead of reading the whole AST, use `some_node.to_raw_ast_debug()` method within the template code to point out pinpointed AST structures. You don't call print(), just add it to the template code and run radar normally on dev mode to see the output
- Strive for the highest detection rates of true positives
- Template rules may not be too generic / match benign patterns / use hard-coded values or non-deterministic behavior
- Some rules may introduce complexities that are not solvable on the rule level, in such cases, try to resolve on this order:
  - Find a workaround on the template code level - BUT ONLY IF IT IS IDOMATIC AND CLEAN
  - See if writing a new a utility function to `api/utils/dsl/dsl_ast_iterator.py` (on RustASTNode) helps significantly, and in a way useful for future rules - if so, proceed to implement the utility function and use it in the template
  - In rare cases, investigate for a core issue on `api/utils/ast.py`
- If a function is not logged or working, it might be failing silently due to the try/catch in the template rule - check if all called methods indeed exist on the node type
- Always debug a single template at a time against a single contract
- If the user provided a command with a specific template and target contract, ALWAYS do your tests on the user provided specific command, don't divert into other test files or methods or templates.

## quality verification of radar template rules
- Every template must have a corresponding unit test in `api/tests/test_templates.py`
- Every template must have a vulnerable example in `api/tests/mocks/<template_name>/bad`
- Every template must have a non-vulnerable example in `api/tests/mocks/<template_name>/good`
- Unit tests must verify that the template detects all issues in the bad example, and does not detect any issues in the good example
- IMPORTANT: it's crucial that the template rules result in a src line that actually points to the core issue in the code, not just somewhere in the function or file, not generic imports, etc.

