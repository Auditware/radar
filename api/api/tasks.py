from pathlib import Path
from api.models import GeneratedAST
from celery import shared_task


@shared_task
def run_scan_task(source_type, source_path, yaml_data):
    try:
        query = {"source_type": source_type, f"{source_type}_path": source_path}
        generated_ast = GeneratedAST.objects.filter(**query).order_by('-created').first()

        # @todo implement real task execution
        print(f"AST ID: {generated_ast.id}, Source Type: {generated_ast.source_type}")
        print(yaml_data)
    except GeneratedAST.DoesNotExist:
        print("No matching GeneratedAST found")
