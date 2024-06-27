from django.contrib import admin
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget
from .models import GeneratedAST


@admin.register(GeneratedAST)
class GeneratedASTAdmin(admin.ModelAdmin):
    list_display = ("source_type", "file_path", "folder_path", "ast")
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }
