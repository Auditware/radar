from pathlib import Path
import yaml
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.tasks import run_scan_task
from utils.ast import (
    generate_anchor_project_ast,
    generate_ast_for_anchor_file,
    generate_anchor_program_ast,
)

from .serializers import GenerateASTSerializer

import logging

logger = logging.getLogger(__name__)


class GenerateASTView(APIView):
    def post(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        source_path = request.data.get(f"{source_type}_path")

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

        ast_data = {}

        source_file_path = Path("/radar_data") / Path(source_path.lstrip("/"))
        if source_type == "file":
            logger.info(f"Generating AST for {source_file_path}")
            try:
                file_ast = generate_ast_for_anchor_file(source_file_path)
                ast_data = {"sources": {}, "metadata": {}}
                ast_data["sources"][str(source_file_path)] = file_ast
            except Exception as e:
                logger.error(e)
                return Response(
                    {"error": "Faild to parse AST from provided source code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif source_type == "folder":
            # User may provide a path to the root of the project, or to a specific prgoram,
            # differentiated by the respective toml file present
            anchor_file = source_file_path / "Anchor.toml"
            xargo_file = source_file_path / "Xargo.toml"

            if xargo_file.exists():
                try:
                    ast_data = generate_anchor_program_ast(source_file_path)
                except Exception as e:
                    logger.error(e)
                    return Response(
                        {
                            "error": "Failed to parse AST from provided program source code"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif anchor_file.exists():
                try:
                    ast_data = generate_anchor_project_ast(source_file_path)
                except Exception as e:
                    logger.error(e)
                    return Response(
                        {
                            "error": "Failed to parse AST from provided program source code"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {
                        "error": "Failed to find Anchor.toml or Xargo.toml in the source path."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer_data = {
            "ast": ast_data,
            "source_type": source_type,
            "file_path": source_path if source_type == "file" else None,
            "folder_path": source_path if source_type == "folder" else None,
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
            templates_path = Path("/radar_data") / Path(templates_path).relative_to("/")
            if not templates_path.exists() or not templates_path.is_dir():
                return Response(
                    {"error": "Invalid templates path"}, status=status.HTTP_400_BAD_REQUEST
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
        
        for yaml_file in yaml_files:
            yaml_data = None
            try:
                with open(yaml_file, 'r') as f:
                    yaml_data = yaml.safe_load(f)
            except:
                return Response(
                    {"error": f"Invalid template provided: {yaml_file}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            if yaml_data is not None:
                run_scan_task.delay(source_type=source_type, source_path=source_path, yaml_data=yaml_data) 

        return Response({"message": "Scan initiated"}, status=status.HTTP_201_CREATED)
