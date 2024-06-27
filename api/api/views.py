from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.ast import generateASTForAnchorFile

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
            return Response(
                {"error": 'source_type must be either "file" or "folder"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ast_data = {}
        if source_type == "file":
            source_file_path = Path("/radar_data") / Path(source_path.lstrip("/"))
            logger.info(f"Generating AST for {source_file_path}")
            try:
                ast_data = generateASTForAnchorFile(source_file_path)
            except Exception as e:
                logger.error(e)
                return Response(
                    {"error": "Faild to parse AST from provided source code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # @todo implement
        elif source_type == "folder":
            raise NotImplementedError("Folder parsing is not implemented yet")

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
