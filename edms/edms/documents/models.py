from django.db import models, transaction
from django.utils.timezone import now

from edms.assets.models import Asset
from edms.common import pdf_helper
from edms.common.basemodels import BaseModel
from edms.common.s3_helper import S3FileManager
from edms.core.models import SoftDeleteModel
from edms.documents.signing_utils import MySignHelper
from edms.notifications.services import NotificationService
from edms.users.models import User
import mimetypes
from django.core.cache import cache
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
import pickle
import copy


# Create your models here.
class Document(SoftDeleteModel, BaseModel):
    SIGNING_DOCUMENT = "signing_document"
    NORMAL_DOCUMENT = "normal_document"
    IN_PROGRESS_SIGNING_DOCUMENT = "in_progress_signing_document"
    COMPLETED_SIGNING_DOCUMENT = "completed_signing_document"
    DOCUMENT_CATEGORY_CHOICES = [
        (SIGNING_DOCUMENT, SIGNING_DOCUMENT),
        (NORMAL_DOCUMENT, NORMAL_DOCUMENT),
        (IN_PROGRESS_SIGNING_DOCUMENT, IN_PROGRESS_SIGNING_DOCUMENT),
        (COMPLETED_SIGNING_DOCUMENT, COMPLETED_SIGNING_DOCUMENT),
    ]

    document_code = models.CharField(max_length=50, unique=True)
    document_title = models.CharField(max_length=255)
    document_summary = models.TextField()
    document_type = models.CharField(max_length=255, blank=True, null=True)
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

    def update_fields(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)

        self.save()

    def associate_assets(self, files, file_type):
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

    @transaction.atomic()
    def send_to_users(self, sender, receivers):
        if self.created_by in receivers:
            raise ValueError("Cannot send the document to the creator.")
        if sender in receivers:
            raise ValueError("Cannot send the document to yourself.")
        document_receivers = []
        actually_receivers = []
        for receiver in receivers:
            if not DocumentReceiver.objects.filter(document=self, receiver=receiver).exists():
                actually_receivers.append(receiver)
                document_receivers.append(
                    DocumentReceiver(
                        document=self,
                        created_by=sender,
                        receiver=receiver
                    )
                )
        if document_receivers:
            document_receivers = DocumentReceiver.objects.bulk_create(document_receivers)
            NotificationService.send_notification_to_users(
                sender=sender,
                receivers=actually_receivers,
                title="Tài liệu mới được gửi đến bạn",
                body=f"Tài liệu '{self.document_title}' đã được gửi đến bạn.",
                image=None,
                data={
                    "urgency_status": self.urgency_status,
                    "document_id": str(self.id)
                }
            )
        return document_receivers

    @transaction.atomic()
    def send_to_organizations(self, sender, organizations):
        receivers_in_orgs = User.objects.filter(organization_unit__in=organizations)

        document_receivers = []
        actually_receivers = []
        for receiver in receivers_in_orgs:
            if receiver == self.created_by:
                continue
            if receiver == sender:
                continue
            if not DocumentReceiver.objects.filter(document=self, receiver=receiver).exists():
                actually_receivers.append(receiver)
                document_receivers.append(
                    DocumentReceiver(
                        document=self,
                        created_by=sender,
                        receiver=receiver
                    )
                )
        if document_receivers:
            document_receivers = DocumentReceiver.objects.bulk_create(document_receivers)
            NotificationService.send_notification_to_users(
                sender=sender,
                receivers=actually_receivers,
                title="Tài liệu mới được gửi đến bạn",
                body=f"Tài liệu '{self.document_title}' đã được gửi đến bạn.",
                image=None,
                data={
                    "urgency_status": self.urgency_status,
                    "document_id": str(self.id)
                }
            )
        return document_receivers

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

    def update_document_signature_flow(self, signers):
        self.signatures.all().delete()
        self.create_document_signature_flow(signers)

    @transaction.atomic
    def start_sign(self, request):
        try:
            # TODO Validate signature stream
            if self.document_category != Document.SIGNING_DOCUMENT:
                raise ValueError("The document cannot be signed because it is not categorized as a signing document.")

            signature_file = Asset.objects.filter(
                file_type=Asset.SIGNATURE_FILE,
                document_id=self.id,
            )

            if not signature_file.exists() or signature_file.count() > 1:
                raise ValueError("Cannot sign document because it requires one signature file.")

            self.update_fields(
                document_category=Document.IN_PROGRESS_SIGNING_DOCUMENT,
                updated_by=request.user,
            )
            # TODO Noti to signer
            NotificationService.send_notification_to_users(
                sender=request.user,
                receivers=[self.signatures.filter(order=1).first().signer],
                title="Yêu cầu ký tài liệu",
                body=f"Tài liệu {self.document_title} cần được ký. Vui lòng kiểm tra và hoàn tất.",
                image=None,
                data={
                    "urgency_status": self.urgency_status,
                    "document_id": str(self.id)
                }
            )
        except Exception as e:
            raise ValueError(f"Failed to update document state: {e}")

    def sign(self, request, client_id, client_secret, base_url, profile_id, access_key, secret_key, region_name, bucket_name):
        if self.document_category != Document.IN_PROGRESS_SIGNING_DOCUMENT:
            raise ValueError(
                "The document cannot be signed because it is not categorized as a in progress signing document."
            )
        document_signature = self.signatures.filter(signer=request.user).first()

        if document_signature.signature_status in [DocumentSignature.SIGNED, DocumentSignature.PENDING, DocumentSignature.REJECTED]:
            raise ValueError("You have SIGNED/PENDING/REJECTED the signing.")

        previous_signatures = self.signatures.filter(
            order__lt=document_signature.order
        ).exclude(
            signature_status=DocumentSignature.SIGNED
        )

        if previous_signatures:
            raise ValueError(
                "The signing process cannot proceed because a previous signer has not completed their signature"
            )

        signature_file = Asset.objects.filter(
            file_type=Asset.SIGNATURE_FILE,
            document_id=self.id,
        ).first()
        if document_signature and signature_file:
            cert_list, access_token = MySignHelper.get_all_certificates(
                user_id=document_signature.signer.external_user_id,
                base_url=base_url,
                client_id=client_id,
                client_secret=client_secret,
                profile_id=profile_id
            )

            if cert_list:
                signature_file_input = signature_file.get_asset_file(
                    access_key=access_key,
                    secret_key=secret_key,
                    region_name=region_name,
                    bucket_name=bucket_name
                )

                origin_file_input = copy.deepcopy(signature_file_input)

                sigpage, signature_box, signature_img = pdf_helper.get_positions_signature(
                    input_pdf=signature_file_input,
                    document_signature=document_signature
                )

                cert = MySignHelper.get_cert509(cert_list[list(cert_list.keys())[0]]['certificates'][0])

                signature_img = S3FileManager.download_image_from_s3(signature_img)

                prep_digest, psi, signed_attrs, output = MySignHelper.prepare_document(
                    file_data=IncrementalPdfFileWriter(origin_file_input),
                    sig_name=f"Signature{document_signature.order}",
                    sigpage=sigpage,
                    signature_box=signature_box,
                    signature_img=signature_img,
                    cert=cert,
                    signer=document_signature.signer,
                )

                hash_list = [MySignHelper.generate_base64_sha256(signed_attrs.dump())]

                sign_hash_response = MySignHelper.sign_hash(
                    hash_list=hash_list,
                    document_id=self.document_code,
                    document_name=MySignHelper.convert_string2base64(self.document_title),
                    client_id=client_id,
                    client_secret=client_secret,
                    credential_id=list(cert_list.keys())[0],
                    base_url=base_url,
                    access_token=access_token
                )

                if not sign_hash_response:
                    raise ValueError("Failed to sign the document.")

                try:
                    document_signature.update_fields(
                        transaction_id=sign_hash_response.get("transactionId"),
                        signature_status=DocumentSignature.PENDING,
                        updated_by=request.user,
                    )

                    cache_key = f"signature:{self.document_code}:{document_signature.id}"
                    cache_data = {
                        'prep_digest': prep_digest,
                        'signed_attrs': signed_attrs.dump(),
                        'psi': psi,
                        'output_handle': output.getbuffer().tobytes(),
                        'cert': cert_list[list(cert_list.keys())[0]]['certificates'][0]
                    }
                    cache.set(cache_key, pickle.dumps(cache_data), timeout=3600)

                except Exception as e:
                    raise ValueError(f"Failed to update document state: {e}")
                return sign_hash_response
            else:
                raise ValueError("No certificates found for the signer.")
        else:
            raise ValueError("No unsigned signer or signature files available.")


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

    def mark_as_read(self):
        self.is_read = True
        self.read_at = now()
        self.updated_by = self.receiver
        self.save()


class DocumentSignature(BaseModel):
    SIGNED = "signed"
    UNSIGNED = "unsigned"
    PENDING = "pending"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    FAILED = "failed"
    SIGNATURE_STATUS_CHOICES = [
        (SIGNED, SIGNED),
        (UNSIGNED, UNSIGNED),
        (PENDING, PENDING),
        (TIMEOUT, TIMEOUT),
        (REJECTED, REJECTED),
        (FAILED, FAILED),
    ]

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
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def update_fields(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)

        self.save()
