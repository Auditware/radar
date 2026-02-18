import os
from pathlib import Path
import yaml
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import GeneratedAST
from api.tasks import run_scan_task
from utils.ast import (
    generate_aggregate_program_ast,
    generate_ast_for_anchor_project,
    generate_ast_for_rust_file,
    generate_ast_for_rust_program,
)
from celery.result import AsyncResult


from .serializers import GenerateASTSerializer

import logging

logger = logging.getLogger(__name__)


class GenerateRustASTView(APIView):
    def post(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        source_path = request.data.get(f"{source_type}_path")
        framework = request.data.get("framework", "unknown")

        if not source_type or not source_path:
            return Response(
                {"error": "Missing required fields: source_type and path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source_type not in ["file", "folder"]:
            logger.error(f"Unrecognized source_type {source_type}")
            return Response(
                {"error": 'source_type must be either "file" or "folder"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_file_path = Path("/radar_data") / Path(source_path.lstrip("/"))
        
        language = "rust"
        if source_type == "file" and source_file_path.suffix == ".sol":
            language = "solidity"
        
        logger.info(f"Language detected: {language}")
        
        if language == "solidity":
            from utils.ast import generate_ast_for_solidity_file
            try:
                file_ast = generate_ast_for_solidity_file(source_file_path)
                ast_data = {"sources": {}, "metadata": {}}
                ast_data = file_ast
            except Exception as e:
                logger.error(e)
                return Response(
                    {"error": f"Failed to parse Solidity AST: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            ast_data = {}

            if source_type == "file":
                logger.info(f"Generating AST for {source_file_path}")
                try:
                    file_ast = generate_ast_for_rust_file(source_file_path)
                    ast_data = {"sources": {}, "metadata": {}}
                    ast_data["sources"][str(source_file_path)] = file_ast
                except Exception as e:
                    logger.error(e)
                    return Response(
                        {"error": "Faild to parse AST from provided source code"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            elif source_type == "folder":
                # Check for Solidity files first - only in src/ for Foundry projects
                if (source_file_path / "foundry.toml").exists():
                    # For Foundry projects, only compile src/ files
                    sol_files = list((source_file_path / "src").rglob("*.sol")) if (source_file_path / "src").exists() else []
                else:
                    # For non-Foundry, include all .sol files
                    sol_files = list(source_file_path.rglob("*.sol"))
                
                # Filter out Foundry test/verification files (only for Foundry projects)
                if (source_file_path / "foundry.toml").exists():
                    sol_files = [
                        f for f in sol_files 
                        if not any(part in f.parts for part in ['test', 'Test', 'certora', 'forge-std'])
                        and not f.stem.endswith('.t')
                    ]
                
                if sol_files:
                    logger.info(f"Found {len(sol_files)} Solidity file(s) at {source_file_path}")
                    language = "solidity"
                    logger.info(f"Language detected: {language}")
                    from utils.solidity_compiler import get_foundry_remappings, compile_solidity_files
                    
                    remappings = None
                    base_path = None
                    
                    if (source_file_path / "foundry.toml").exists():
                        logger.info("Detected Foundry project, extracting remappings...")
                        remappings = get_foundry_remappings(source_file_path)
                        base_path = source_file_path
                    
                    try:
                        # Compile all files together for proper import resolution
                        compiled_ast = compile_solidity_files(sol_files, remappings=remappings, base_path=base_path)
                        ast_data = compiled_ast
                    except Exception as e:
                        logger.error(e)
                        return Response(
                            {"error": f"Failed to parse Solidity AST: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                # User may provide a path to the root of the project, or to a specific prgoram,
                # differentiated by the respective toml file present
                elif (source_file_path / "Xargo.toml").exists():
                    try:
                        ast_data = generate_ast_for_rust_program(source_file_path)
                    except Exception as e:
                        logger.error(e)
                        return Response(
                            {
                                "error": f"Failed to parse AST from provided program source code: {str(e)}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                elif (source_file_path / "Anchor.toml").exists():
                    try:
                        ast_data = generate_ast_for_anchor_project(source_file_path)
                    except Exception as e:
                        logger.error(e)
                        return Response(
                            {
                                "error": f"Failed to parse AST from provided program source code: {str(e)}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # last check for multiple programs within a folder, or quit trying
                else:
                    try:
                        ast_data = generate_aggregate_program_ast(source_file_path)
                        if ast_data is None:
                            raise ValueError(
                                "No Cargo.toml files found in any subdirectories."
                            )
                    except Exception as e:
                        logger.error(e)
                        return Response(
                            {
                                "error": f"Failed to process source path {source_file_path}: {str(e)}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

        serializer_data = {
            "ast": ast_data,
            "source_type": source_type,
            "file_path": source_path if source_type == "file" else None,
            "folder_path": source_path if source_type == "folder" else None,
            "language": language,
            "framework": framework,
        }
        serializer = GenerateASTSerializer(data=serializer_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RunScanView(APIView):
    def post(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        source_path = request.data.get(f"{source_type}_path")
        templates_path = request.data.get("templates_path")

        if not source_path or not source_type:
            return Response(
                {"error": "Missing source type or path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if templates_path:
            # Handle both absolute and relative template paths
            if Path(templates_path).is_absolute():
                templates_path = Path("/radar_data") / Path(templates_path).relative_to("/")
            else:
                templates_path = Path("/radar_data") / templates_path
            if not templates_path.exists() or not templates_path.is_dir():
                return Response(
                    {"error": "Invalid templates path"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            yaml_files = list(templates_path.rglob("*.yaml"))
        else:
            templates_path = Path("builtin_templates").absolute()
            yaml_files = list(templates_path.rglob("*.yaml"))

        if not yaml_files:
            return Response(
                {"error": "No YAML files found at the specified templates path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task_ids = []
        query = {"source_type": source_type, f"{source_type}_path": source_path}
        generated_ast = (
            GeneratedAST.objects.filter(**query).order_by("-created").first()
        )
        
        # Get the detected language and framework from the AST
        detected_language = generated_ast.language if generated_ast else "rust"
        detected_framework = generated_ast.framework if generated_ast else "unknown"

        for yaml_file in yaml_files:
            yaml_data = None
            try:
                with open(yaml_file, "r") as f:
                    yaml_data = yaml.safe_load(f)
            except:
                return Response(
                    {"error": f"Invalid template provided: {yaml_file}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if yaml_data is not None:
                # Filter templates by language - only run templates that match detected language
                template_language = yaml_data.get("language", "rust")
                if template_language != detected_language:
                    continue
                
                # Filter by framework/accent for rust templates
                template_accent = yaml_data.get("accent", "")
                if detected_language == "rust" and template_accent and detected_framework != "unknown":
                    if template_accent != detected_framework:
                        continue
                
                result = run_scan_task.apply_async(
                    kwargs={
                        "yaml_data": yaml_data,
                        "generated_ast_id": generated_ast.id,
                    },
                    task_id=yaml_data["name"],
                )
                task_ids.append(result.id)

        generated_ast.task_ids = task_ids
        generated_ast.save()

        return Response({"message": "Scan initiated"}, status=status.HTTP_201_CREATED)


class PollResultsView(APIView):
    def get(self, request, *args, **kwargs):
        source_type = request.GET.get("source_type")
        source_path = request.GET.get(f"{source_type}_path")

        # Validate the required parameters
        if not source_type or not source_path:
            return Response(
                {"error": "Missing required fields: source_type and path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = {"source_type": source_type, f"{source_type}_path": source_path}
        generated_ast = (
            GeneratedAST.objects.filter(**query).order_by("-created").first()
        )

        if not generated_ast:
            return Response(
                {"error": "GeneratedAST not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = []
        all_done = True

        for task_id in generated_ast.task_ids:
            result = AsyncResult(task_id)
            if result.ready():
                if result.successful():
                    task_result = result.get()
                    task_result_results = task_result.get("results")
                    if task_result_results and (
                        task_result_results.get("locations")
                        or task_result_results.get("debug")
                    ):
                        results.append(task_result_results)
                else:
                    print(dir(result))
                    return Response(
                        {
                            "error": f"Task '{task_id}' failed",
                            "details": str(result.result),
                            "traceback": result.traceback.split("\n "),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                all_done = False

        if all_done:
            template_count = len(generated_ast.task_ids)
            return Response({
                "results": results,
                "template_count": template_count
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"status": "Tasks are still running."}, status=status.HTTP_202_ACCEPTED
            )
