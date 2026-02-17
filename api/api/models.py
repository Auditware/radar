from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _


class ScoreLevel(models.TextChoices):
    INFO = "Info", _("Info")
    LOW = "Low", _("Low")
    MEDIUM = "Medium", _("Medium")
    HIGH = "High", _("High")
    CRITICAL = "Critical", _("Critical")


class GeneratedAST(models.Model):
    ast = models.JSONField(blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    task_ids = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    language = models.CharField(max_length=50, default="rust", blank=True, null=True)
    framework = models.CharField(max_length=50, default="unknown", blank=True, null=True)

    class SourceTypeOptions(models.TextChoices):
        FILE = "file"
        FOLDER = "folder"

    source_type = models.CharField(choices=SourceTypeOptions.choices)

    def __str__(self):
        if self.source_type == self.SourceTypeOptions.FILE:
            return self.file_path if self.file_path else "Bad filepath"
        else:
            return self.folder_path if self.folder_path else "Bad folderpath"