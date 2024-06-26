from django.contrib import admin
from .models import GeneratedAST


@admin.register(GeneratedAST)
class GeneratedASTAdmin(admin.ModelAdmin):
    list_display = ("file_path", "ast")
