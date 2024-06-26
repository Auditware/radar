from django.db import models


class GeneratedAST(models.Model):
    ast = models.JSONField(blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    class SourceTypeOptions(models.TextChoices):
        FILE = "file"
        FOLDER = "folder"

    source_type = models.CharField(choices=SourceTypeOptions.choices)

    def __str__(self):
        if self.source_type == self.SourceTypeOptions.FILE:
            return self.file_path if self.file_path else "Bad filepath"
        else:
            return self.folder_path if self.folder_path else "Bad folderpath"
