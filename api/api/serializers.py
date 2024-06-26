from rest_framework import serializers
from .models import GeneratedAST


class GenerateASTSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedAST
        fields = ["ast", "source_type", "file_path", "folder_path"]
