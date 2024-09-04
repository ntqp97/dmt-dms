import os
import uuid

from django.db import models

from edms.common.basemodels import BaseModel


def get_path_files(instance, filename):
    return os.path.join(
        f"uploads/{instance.created_by_id}/{instance.file_type}/asset-{uuid.uuid4().hex}/",
        filename,
    )


# Create your models here.
class Asset(BaseModel):
    ATTACHMENT = "attachment"
    APPENDIX = "appendix"
    FILE_TYPE_CHOICES = [(ATTACHMENT, ATTACHMENT), (APPENDIX, APPENDIX)]

    document = models.ForeignKey(
        "documents.Document",
        related_name="related_files",
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to=get_path_files,
        blank=True,
        null=True,
        default=None,
    )
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=255)
    asset_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=FILE_TYPE_CHOICES,
        default=ATTACHMENT,
    )
