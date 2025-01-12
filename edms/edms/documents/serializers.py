import logging
import os
import uuid

from django.utils import timezone
from rest_framework import serializers

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.upload_helper import validate_file_type
from edms.documents.models import Document, DocumentSignature
from edms.documents.models import DocumentReceiver
from edms.notifications.services import NotificationService
from edms.organization.models import OrganizationUnit
from edms.users.api.serializers import UserSerializer
from edms.users.models import User

myapp_logger = logging.getLogger("django")


class MarkAsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentReceiver
        fields = ["is_read", "read_at"]
        read_only_fields = ["read_at", "is_read"]

    def update(self, instance, validated_data):
        instance.is_read = True
        instance.read_at = timezone.now()
        instance.save()
        return instance


class DocumentReceiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentReceiver
        fields = ["document", "id", "receiver", "is_read", "read_at"]


class DocumentSignatureSerializer(serializers.ModelSerializer):
    signer_id = serializers.IntegerField(
        required=True,
        write_only=True
    )
    is_signature_visible = serializers.BooleanField(required=True)
    order = serializers.IntegerField(required=True)
    signer = UserSerializer(read_only=True)

    class Meta:
        model = DocumentSignature
        fields = ["document", "signer_id", "signer", "is_signature_visible", "signature_status", "order"]
        read_only_fields = ["signature_status", "document"]


class SendDocumentSerializer(serializers.Serializer):
    recipient_type = serializers.ChoiceField(choices=[('user', 'User'), ('organization', 'Organization')])
    recipient_id = serializers.CharField()

    def validate(self, data):
        document = self.context['document']
        request = self.context['request']
        recipient_type = data.get('recipient_type')
        recipient_ids = list(map(int, data.get("recipient_id", []).split(',')))

        if document.document_category not in [Document.NORMAL_DOCUMENT, Document.COMPLETED_SIGNING_DOCUMENT]:
            raise serializers.ValidationError(
                {"detail": "This document category does not allow sending."},
            )

        if recipient_type == 'user':
            if request.user.id in recipient_ids:
                raise serializers.ValidationError(
                    {"detail": "You cannot include yourself as a receiver."},
                )
            invalid_users = User.objects.filter(id__in=recipient_ids).values_list('id', flat=True)
            missing_users = set(recipient_ids) - set(invalid_users)
            if missing_users:
                raise serializers.ValidationError(
                    {"detail": f"User(s) with id(s) {', '.join(map(str, missing_users))} not found."}
                )
            already_received = DocumentReceiver.objects.filter(
                document=document,
                receiver__id__in=recipient_ids
            ).values_list('receiver__id', flat=True)

            if already_received:
                raise serializers.ValidationError(
                    {"detail": f"User(s) with id(s) {', '.join(map(str, already_received))} has/have already received this document."}
                )

        elif recipient_type == 'organization':
            invalid_organizationunits = OrganizationUnit.objects.filter(
                id__in=recipient_ids
            ).values_list('id', flat=True)
            missing_organizationunits = set(recipient_ids) - set(invalid_organizationunits)
            if missing_organizationunits:
                raise serializers.ValidationError(
                    {"detail": f"Organization(s) with id(s) {', '.join(map(str, missing_organizationunits))} not found."}
                )
        return data


class BaseDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = [
            "id", "document_code", "document_title", "document_summary",
            "document_type", "urgency_status", "document_form",
            "security_type", "publish_type", "document_number_reference_code",
            "sector", "processing_status", "document_category"
        ]


class DocumentSerializer(serializers.ModelSerializer):
    attachment_document_ids = serializers.CharField(
        required=False,
        write_only=True,
    )
    attachment_documents = BaseDocumentSerializer(
        many=True,
        read_only=True,
    )
    receivers_ids = serializers.CharField(
        required=False,
        write_only=True,
    )
    signers_flow = DocumentSignatureSerializer(
        required=False,
        many=True,
    )
    receivers = UserSerializer(
        many=True,
        read_only=True,
    )
    sender = UserSerializer(
        read_only=True,
    )
    arrival_at = serializers.IntegerField(
        read_only=True,
    )
    attachment_files = serializers.ListField(
        required=False,
        child=serializers.FileField(),
    )
    appendix_files = serializers.ListField(
        required=False,
        child=serializers.FileField(),
    )
    signature_files = serializers.ListField(
        required=False,
        child=serializers.FileField(),
    )

    class Meta:
        model = Document
        fields = [
            "id",
            "document_code",
            "document_title",
            "document_summary",
            "document_type",
            "urgency_status",
            "document_form",
            "signers_flow",
            "receivers",
            "receivers_ids",
            "sender",
            "arrival_at",
            "security_type",
            "document_processing_deadline_at",
            "publish_type",
            "document_number_reference_code",
            "sector",
            "processing_status",
            "attachment_files",
            "appendix_files",
            "signature_files",
            "attachment_document_ids",
            "attachment_documents",
            "document_category",
        ]
        read_only_fields = ["document_code", "document_category"]

    # def validate_file_type(self, file, allowed_extensions):
    #     _, file_extension = os.path.splitext(file.name)
    #     if file_extension.replace(".", "") not in allowed_extensions:
    #         raise serializers.ValidationError(
    #             {"detail": f"Unsupported file type: {file_extension}."},
    #         )
    #     return file

    def validate(self, data):
        attachment_files = data.get("attachment_files", [])
        appendix_files = data.get("appendix_files", [])
        signature_files = data.get("signature_files", [])
        receivers_ids = data.get("receivers_ids")
        receivers_pks = list(map(int, receivers_ids.split(','))) if receivers_ids else []
        user = self.context["request"].user
        if user.id in receivers_pks:
            raise serializers.ValidationError(
                {"detail": "You cannot include yourself as a receiver."},
            )

        signers_data = data.get("signers_flow", self.context.get("signers_flow", []))
        serializer = DocumentSignatureSerializer(data=signers_data, many=True)
        if serializer.is_valid():
            data['signers_flow'] = signers_data
        else:
            raise serializers.ValidationError(
                {"detail": f"{serializer.errors}."},
            )

        if signature_files:
            attachment_document_ids = data.get("attachment_document_ids")
            attachment_document_ids = list(map(int, attachment_document_ids.split(','))) if attachment_document_ids else []

            if len(signature_files) > 1:
                raise serializers.ValidationError(
                    {"detail": "You can only include one signature file."},
                )
            if not signers_data:
                raise serializers.ValidationError(
                    {"detail": "Signers are required when including a signature file."},
                )

        # if not attachment_files and not appendix_files and not signature_files:
        #     raise serializers.ValidationError(
        #         {
        #             "detail": "At least one of the fields 'files' must be provided.",
        #         },
        #     )

        # Validate file types
        for file in attachment_files:
            allowed_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
            validate_file_type(file, allowed_extensions)

        for file in appendix_files:
            allowed_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
            validate_file_type(file, allowed_extensions)

        for file in signature_files:
            allowed_extensions = ["pdf"]
            validate_file_type(file, allowed_extensions)

        return data

    def create(self, validated_data):
        request = self.context["request"]
        attachment_files = validated_data.pop("attachment_files", [])
        appendix_files = validated_data.pop("appendix_files", [])
        signature_files = validated_data.pop("signature_files", [])
        receivers_ids = validated_data.pop("receivers_ids", [])
        receivers_pks = list(map(int, receivers_ids.split(','))) if receivers_ids else []
        receivers = []
        signers_flow = validated_data.pop("signers_flow", [])
        attachment_document_ids = validated_data.pop("attachment_document_ids", [])
        attachment_document_ids = list(map(int, attachment_document_ids.split(','))) if attachment_document_ids else []

        if not attachment_files and not appendix_files and not signature_files:
            raise serializers.ValidationError(
                {
                    "detail": "At least one of the fields 'files' must be provided.",
                },
            )

        validated_data["document_code"] = uuid.uuid4()
        validated_data["document_category"] = (
            Document.SIGNING_DOCUMENT
            if signature_files
            else Document.NORMAL_DOCUMENT
        )

        document = Document.objects.create(**validated_data)

        if not signature_files:
            receivers = User.objects.filter(pk__in=receivers_pks)
            missing_receivers = set(receivers_pks) - set(
                receivers.values_list("pk", flat=True),
            )
            if missing_receivers:
                raise serializers.ValidationError(
                    {"detail": f"Users with Pks {missing_receivers} do not exist."},
                )
            document.associate_receivers(receivers)
        else:
            attachment_document = Document.objects.filter(pk__in=attachment_document_ids)
            document.attachment_documents.add(*attachment_document)
            document.create_document_signature_flow(signers=signers_flow)

        document.associate_assets(attachment_files, Asset.ATTACHMENT)
        document.associate_assets(appendix_files, Asset.APPENDIX)
        document.associate_assets(signature_files, Asset.SIGNATURE_FILE)
        NotificationService.send_notification_to_users(
            sender=request.user,
            receivers=receivers,
            title="Tài liệu mới được gửi đến bạn",
            body=f"Tài liệu '{document.document_title}' đã được gửi đến bạn.",
            image=None,
            data={
                "urgency_status": document.urgency_status,
                "document_id": str(document.id)
            }
        )
        return document

    def update(self, instance, validated_data):
        attachment_files = validated_data.pop("attachment_files", [])
        appendix_files = validated_data.pop("appendix_files", [])
        signature_files = validated_data.pop("signature_files", [])
        signers_flow = validated_data.pop("signers_flow", [])
        _ = validated_data.pop("receivers_ids", [])
        attachment_document_ids = validated_data.pop("attachment_document_ids", [])
        attachment_document_ids = list(map(int, attachment_document_ids.split(','))) if attachment_document_ids else []

        old_signature_files = Asset.objects.filter(
            file_type=Asset.SIGNATURE_FILE,
            document_id=instance.id,
        ).exists()

        if signature_files and old_signature_files:
            raise serializers.ValidationError(
                {"detail": "Signature files already exist. You cannot upload another one."},
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        attachment_document = Document.objects.filter(pk__in=attachment_document_ids)
        instance.attachment_documents.set(attachment_document)
        instance.update_document_signature_flow(signers=signers_flow)

        instance.associate_assets(attachment_files, Asset.ATTACHMENT)
        instance.associate_assets(appendix_files, Asset.APPENDIX)
        instance.associate_assets(signature_files, Asset.SIGNATURE_FILE)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request', None)
        data = super().to_representation(instance)
        data['signers_flow'] = DocumentSignatureSerializer(
            instance.signatures.all(),
            many=True,
            context=self.context
        ).data
        if request:
            if instance.created_by.id == request.user.id:
                data["sender"] = UserSerializer(
                    request.user,
                    context=self.context
                ).data
                data["arrival_at"] = int((float(instance.created_at.timestamp())) * 1000)
            else:
                document_signer_or_receiver = (
                    instance.signatures.filter(signer_id=request.user.id).first() or
                    instance.document_receivers.filter(receiver_id=request.user.id).first()
                )

                if document_signer_or_receiver:
                    data["sender"] = UserSerializer(
                        document_signer_or_receiver.created_by,
                        context=self.context
                    ).data
                    data["arrival_at"] = int((float(document_signer_or_receiver.created_at.timestamp())) * 1000)
        attachment_files = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.ATTACHMENT,
                document_id=instance.id,
            ),
            many=True,
            context=self.context
        ).data
        appendix_files = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.APPENDIX,
                document_id=instance.id,
            ),
            many=True,
            context=self.context
        ).data
        signature_files = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.SIGNATURE_FILE,
                document_id=instance.id,
            ),
            many=True,
            context=self.context
        ).data

        data["attachment_files"] = attachment_files
        data["appendix_files"] = appendix_files
        data["signature_files"] = signature_files
        return data
