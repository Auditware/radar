# What `ast.json` actually contains

## Two files, not one

`--ast` does not add an `ast` field to the results file. It writes a second file:

```bash
./radar --dev -p ./contract --ast -o out.json
# out.json  → findings
# ast.json  → AST, written beside out.json
```

With no `-o`, both land in the current directory as `output.json` and `ast.json`.

## Shape

Keyed on `sources`, one entry per parsed file, each holding raw parser output plus metadata:

```json
{
  "metadata": { "anchor_toml_path": "..." },
  "sources": {
    "/radar_data/contract/programs/x/src/lib.rs": {
      "ast": [ ... ],
      "metadata": { "program_info": { "name": "x", "version": "0.1.0" } }
    }
  }
}
```

## Rust nodes are syn-serde, so the keys are snake_case

There is no `ItemFn`, `ExprMethodCall`, or `Attribute` in this file. Top-level items appear as `use`, `mod`, `struct`, `macro`; functions as `fn`; calls as `method_call`; and so on. A real fragment:

```json
{
  "vis": "pub",
  "ident": "log_message",
  "inputs": [
    { "typed": { "pat": { "ident": {
        "ident": "ctx",
        "src": { "file": ".../lib.rs", "line": 7, "start_col": 19, "end_col": 22 }
    } } } }
  ]
}
```

`src` carries the location every finding is built from: `file`, `line`, `start_col`, `end_col`. Spans are resolved by scanning the source text for each identifier, not taken from the parser - which is why `tests/test_span_accuracy.py` exists, and why an identifier that never appears literally in the source (a synthesized `doc` attribute, for example) has no usable span.

Solidity ASTs are solc output, with `node_type` and a `src` string that the DSL resolves into `src_calculated`.

## `access_path` and `children` are not in the file

The hierarchy the DSL queries - `access_path`, `children`, `parent` - is built by `parse_ast()` at rule-execution time from the flat parser output. Searching `ast.json` for `access_path` finds nothing.

To see the enriched view a rule actually sees, call it from inside the rule and run the scan:

```python
some_nodes.to_raw_ast_debug()   # prints; do not wrap in print()
```

Its output appears in the finding's `debug` field, and on stdout in `--dev` mode.

## Practical notes

- Scope large projects with `-s/--source` (a subdirectory or a single file) rather than post-filtering.
- Radar skips files it cannot parse, so an empty `sources` usually means a parse failure, not an empty contract - run with `--dev` to see it.
- `--ast` always writes JSON regardless of the `-o` extension; the extension only controls the findings format.
