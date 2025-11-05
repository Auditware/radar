This is a reusable prompt to guide users on prompting new radar utility creation.

Prompt inputs:
- Reference to a relevant ast.json
- Reference to a radar template

If one of the prompt inputs are missing, stop to guide the user on how to fill the missing piece before continuing.

Prompt:
Given referenced ast.json and radar template, read `api/utils/dsl/dsl_ast_iterator.py` and understand that radar utils are mechanisms to search relations or heuristics across ast nodes. On that file, add a util function, aimed at assisting what the user's trying to accomplish on the radar template.
- Read referenced ast and find instances of node types user is trying to locate using the util.
- If there's already an equivalent util, see if it's faulty and just needs small tweaks.
- If not, write one using practices followed on the other utils on that file, like traversal.
- To test, only use the referenced template file and referenced ast.
- If you can't find on that specific data, reinspect what might go wrong.
- You can flush out specific parts from the AST, in radar-AST format (with access_path and other refinements that might be done) via calling `to_raw_ast_debug()` from within the template.
- Don't create a template that will duplicate the existing ones under `api/builtin_templates`, either rename to highlight the specific focus of the heuristic search, or add support in existing template - whichever makes more sense