from django.db import models

from edms.assets.models import Asset
from edms.common.basemodels import BaseModel


# Create your models here.
class Document(BaseModel):
    document_code = models.CharField(max_length=50, unique=True)
    document_title = models.CharField(max_length=255)
    document_summary = models.TextField()
    document_type = models.CharField(max_length=255)
    urgency_status = models.CharField(max_length=255)
    document_form = models.CharField(max_length=255)
    receivers = models.ManyToManyField(
        "users.User",
        through="DocumentReceiver",
        through_fields=("document", "receiver"),
    )
    security_type = models.CharField(max_length=255)
    document_processing_deadline_at = models.BigIntegerField()
    publish_type = models.CharField(max_length=255)
    document_number_reference_code = models.CharField(max_length=255)
    sector = models.CharField(max_length=255)
    processing_status = models.CharField(max_length=255)
    files = models.ManyToManyField("assets.Asset", related_name="document_assets")

    def associate_assets(self, files, file_type):
        Asset.objects.bulk_create(
            [
                Asset(
                    document=self,
                    file_type=file_type,
                    file=file,
                    size=file.size,
                    asset_name=file.name,
                    mime_type=file.content_type,
                    created_by=self.created_by,
                )
                for file in files
            ],
        )

    def send_to_user(self, sender, receiver):
        if receiver == self.created_by:
            raise ValueError("Cannot send the document to the creator.")
        if receiver == sender:
            raise ValueError("Cannot send the document to yourself.")

        return DocumentReceiver.objects.create(
            document=self,
            created_by=sender,
            receiver=receiver
        )

    def send_to_organization(self, sender, organization):
        from edms.users.models import User

        receivers_in_org = User.objects.filter(organization_unit=organization)
        document_receivers = []
        for receiver in receivers_in_org:
            if receiver == self.created_by:
                continue
            if receiver == sender:
                continue
            if not DocumentReceiver.objects.filter(document=self, receiver=receiver).exists():
                document_receivers.append(
                    DocumentReceiver(
                        document=self,
                        created_by=sender,
                        receiver=receiver
                    )
                )

        return document_receivers if not document_receivers else DocumentReceiver.objects.bulk_create(document_receivers)


class DocumentReceiver(BaseModel):
    document = models.ForeignKey(
        "documents.Document",
        related_name="document_receivers",
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        "users.User",
        related_name="received_documents",
        on_delete=models.CASCADE,
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
