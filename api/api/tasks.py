from api.models import GeneratedAST
from celery import shared_task
from utils.dsl.dsl import extract_json_output, inject_code_lines, process_template_outputs, wrapped_exec


@shared_task
def run_scan_task(yaml_data, generated_ast_id):
    task_result = {
        "name": yaml_data["name"],
        "severity": yaml_data["severity"],
        "certainty": yaml_data["certainty"],
        "description": yaml_data["description"],
    }

    try:
        generated_ast = GeneratedAST.objects.get(id=generated_ast_id)
    except GeneratedAST.DoesNotExist:
        print("[e] No matching GeneratedAST found")
        task_result["error"] = "No matching GeneratedAST found"
        return task_result

    code = yaml_data["rule"]
    template_language = yaml_data.get("language", "rust")
    code = inject_code_lines(code, [f"ast = parse_ast({generated_ast.ast}, '{template_language}').items()"])

    try:
        template_outputs = wrapped_exec(code)
        task_result["results"] = process_template_outputs(template_outputs, yaml_data)
    except Exception as exc:
        # A template that raises must not vanish (its findings would silently be
        # zero) nor abort the whole scan. Record the error, keep other templates
        # running, and let the controller surface it and exit non-zero.
        print(f"[e] Template '{yaml_data.get('name')}' failed: {exc}")
        task_result["error"] = f"{type(exc).__name__}: {exc}"

    return task_result
