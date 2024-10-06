from django.db import models

from edms.assets.models import Asset
from edms.common.basemodels import BaseModel
from edms.users.models import User


# Create your models here.
class Document(BaseModel):
    SIGNING_DOCUMENT = "signing_document"
    NORMAL_DOCUMENT = "normal_document"
    DOCUMENT_CATEGORY_CHOICES = [(SIGNING_DOCUMENT, SIGNING_DOCUMENT), (NORMAL_DOCUMENT, NORMAL_DOCUMENT)]

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
    signers = models.ManyToManyField(
        "users.User",
        through="DocumentSignature",
        through_fields=("document", "signer"),
        related_name="signed_documents",
    )
    security_type = models.CharField(max_length=255)
    document_processing_deadline_at = models.BigIntegerField()
    publish_type = models.CharField(max_length=255)
    document_number_reference_code = models.CharField(max_length=255)
    sector = models.CharField(max_length=255)
    processing_status = models.CharField(max_length=255)
    document_category = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=DOCUMENT_CATEGORY_CHOICES,
        default=NORMAL_DOCUMENT,
    )
    files = models.ManyToManyField("assets.Asset", related_name="document_assets")
    attachment_documents = models.ManyToManyField(
        "self",
        blank=True,
        related_name="attached_documents",
        symmetrical=False
    )

    def associate_assets(self, files, file_type):
        import mimetypes
        Asset.objects.bulk_create(
            [
                Asset(
                    document=self,
                    file_type=file_type,
                    file=file,
                    size=file.size,
                    asset_name=file.name,
                    mime_type=(
                        mimetypes.guess_type(file.name)[0]
                        if mimetypes.guess_type(file.name)[0]
                        else file.content_type
                    ),
                    created_by=self.created_by,
                )
                for file in files
            ],
        )

    def associate_receivers(self, receivers):
        DocumentReceiver.objects.bulk_create(
            [
                DocumentReceiver(
                    document=self,
                    created_by=self.created_by,
                    receiver=receiver
                )
                for receiver in receivers
            ],
        )

    def send_to_users(self, sender, receivers):
        if self.created_by in receivers:
            raise ValueError("Cannot send the document to the creator.")
        if sender in receivers:
            raise ValueError("Cannot send the document to yourself.")
        document_receivers = []
        for receiver in receivers:
            if not DocumentReceiver.objects.filter(document=self, receiver=receiver).exists():
                document_receivers.append(
                    DocumentReceiver(
                        document=self,
                        created_by=sender,
                        receiver=receiver
                    )
                )
        return document_receivers if not document_receivers else DocumentReceiver.objects.bulk_create(document_receivers)

    def send_to_organizations(self, sender, organizations):
        receivers_in_orgs = User.objects.filter(organization_unit__in=organizations)

        document_receivers = []
        for receiver in receivers_in_orgs:
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

    def create_document_signature_flow(self, signers):
        DocumentSignature.objects.bulk_create(
            [
                DocumentSignature(
                    document=self,
                    created_by=self.created_by,
                    is_signature_visible=signer['is_signature_visible'],
                    signer=User.objects.get(id=signer['signer_id']),
                    order=signer['order']
                )
                for signer in signers
            ]
        )


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


class DocumentSignature(BaseModel):
    SIGNED = "signed"
    UNSIGNED = "unsigned"
    SIGNATURE_STATUS_CHOICES = [(SIGNED, SIGNED), (UNSIGNED, UNSIGNED)]

    document = models.ForeignKey(
        "documents.Document",
        related_name="signatures",
        on_delete=models.CASCADE,
    )

    signer = models.ForeignKey(
        "users.User",
        related_name="signature_documents",
        on_delete=models.CASCADE
    )

    order = models.PositiveIntegerField()

    signature_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=SIGNATURE_STATUS_CHOICES,
        default=UNSIGNED
    )
    is_signature_visible = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
