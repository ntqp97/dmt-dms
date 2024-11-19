from django.db import models

from edms.common.basemodels import BaseModel


# Create your models here.
class Option(BaseModel):
    SECTOR = "sector"
    DOCUMENT_FORM = "document_form"
    OPTION_TYPE_CHOICES = [
        (SECTOR, SECTOR),
        (DOCUMENT_FORM, DOCUMENT_FORM),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=100, choices=OPTION_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.type})"
