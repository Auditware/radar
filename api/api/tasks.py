from api.models import GeneratedAST
from celery import shared_task
from utils.dsl.dsl import extract_json_output, inject_code_lines, process_template_outputs, wrapped_exec


@shared_task
def run_scan_task(yaml_data, generated_ast_id):
    generated_ast = GeneratedAST.objects.get(id=generated_ast_id)
    try:
        print(f"AST ID: {generated_ast.id}, Source Type: {generated_ast.source_type}")
        task_result = {
            "name": yaml_data["name"],
            "severity": yaml_data["severity"],
            "certainty": yaml_data["certainty"],
            "description": yaml_data["description"],
        }

        code = yaml_data["rule"]
        code = inject_code_lines(code, [f"ast = {generated_ast.ast}"])

        template_outputs = wrapped_exec(code)

        # Save to task results backend and end task successfully
        task_result["results"] = process_template_outputs(template_outputs, yaml_data)
        return task_result

    except GeneratedAST.DoesNotExist:
        print(f"[e] No matching GeneratedAST found")
