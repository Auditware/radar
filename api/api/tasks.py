from api.models import GeneratedAST
from celery import shared_task
from utils.dsl import extract_json_output, inject_code_lines, wrapped_exec


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

        # Iterate over outputs, treat only ast nodes (dict types with an 'ident' & 'src' key on the top level)
        finding_data = {
            "name": yaml_data["name"],
            "description": yaml_data["description"],
            "severity": yaml_data["severity"],
            "certainty": yaml_data["certainty"],
            "locations": [],
        }
        for output in template_outputs:
            valid_output = extract_json_output(output)
            if valid_output is not None:
                print("[i] Finding-valid printed output detected")
                src = valid_output["src"]
                location = f"{src['file']}:{src['line']}:{src['start_col']}-{src['end_col']}"
                finding_data["locations"].append(location)

        # Save to task results backend and end task successfully
        task_result["results"] = finding_data
        return task_result

    except GeneratedAST.DoesNotExist:
        print(f"[e] No matching GeneratedAST found")
