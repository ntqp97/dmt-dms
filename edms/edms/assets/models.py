import os
import uuid
from datetime import datetime

from django.db import models

from edms.common.basemodels import BaseModel
from rest_framework.generics import get_object_or_404

from edms.common.s3_helper import S3FileManager


def get_path_files(instance, filename):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    return os.path.join(
        f"uploads/{instance.created_by_id}/{year}/{month}/{day}/{instance.file_type}/asset-{uuid.uuid4().hex}/",
        filename,
    )


# Create your models here.
class Asset(BaseModel):
    ATTACHMENT = "attachment"
    APPENDIX = "appendix"
    SIGNATURE_FILE = "signature_file"
    SIGNATURE_IMAGE = "signature_image"
    FILE_TYPE_CHOICES = [
        (ATTACHMENT, ATTACHMENT),
        (APPENDIX, APPENDIX),
        (SIGNATURE_FILE, SIGNATURE_FILE),
        (SIGNATURE_IMAGE, SIGNATURE_IMAGE),
    ]

    document = models.ForeignKey(
        "documents.Document",
        related_name="related_files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meeting_schedule = models.ForeignKey(
        "meeting_schedule.MeetingSchedule",
        related_name="meeting_schedule_files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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

    def get_asset_file(self, access_key, secret_key, region_name, bucket_name):
        s3_client = S3FileManager.s3_connection(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name
        )

        asset_file = S3FileManager.get_pdf_from_s3(
            bucket_name=bucket_name,
            file_key=self.file.name,
            s3_client=s3_client
        )
        return asset_file
