import logging
import os
import uuid

from django.utils import timezone
from rest_framework import serializers

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.documents.models import Document
from edms.documents.models import DocumentReceiver
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


class SendDocumentSerializer(serializers.Serializer):
    recipient_type = serializers.ChoiceField(choices=[('user', 'User'), ('organization', 'Organization')])
    recipient_id = serializers.IntegerField()

    def validate(self, data):
        document = self.context['document']
        recipient_type = data.get('recipient_type')
        recipient_id = data.get('recipient_id')

        if recipient_type == 'user':
            try:
                user = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"detail": "User not found"}
                )

            if DocumentReceiver.objects.filter(document=document, receiver=user).exists():
                raise serializers.ValidationError({"detail": "User has already received this document."})

        elif recipient_type == 'organization':
            if not OrganizationUnit.objects.filter(id=recipient_id).exists():
                raise serializers.ValidationError(
                    {"detail": "Organization not found"}
                )
            # try:
            #     organization = OrganizationUnit.objects.get(id=recipient_id)
            # except OrganizationUnit.DoesNotExist:
            #     raise serializers.ValidationError(
            #         {"detail": "Organization not found"}
            #     )
            # receivers_in_org = User.objects.filter(organization_unit=organization)
            # for receiver in receivers_in_org:
            #     if DocumentReceiver.objects.filter(document=document, receiver=receiver).exists():
            #         raise serializers.ValidationError(
            #             {"detail": f"User {receiver.name} in organization has already received this document."}
            #         )
        return data


class DocumentSerializer(serializers.ModelSerializer):
    receivers_ids = serializers.CharField(
        required=False,
        write_only=True,
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
        ]
        read_only_fields = ["document_code"]

    def validate_file_type(self, file):
        allowed_extensions = ["pdf", "doc", "docx", "jpeg"]
        _, file_extension = os.path.splitext(file.name)
        if file_extension.replace(".", "") not in allowed_extensions:
            raise serializers.ValidationError(
                {"detail": f"Unsupported file type: {file_extension}."},
            )
        return file

    def validate(self, data):
        attachment_files = data.get("attachment_files", [])
        appendix_files = data.get("appendix_files", [])
        receivers_pks = list(map(int, data.get("receivers_ids", []).split(',')))

        user = self.context["request"].user
        if user.id in receivers_pks:
            raise serializers.ValidationError(
                {"receivers": "You cannot include yourself as a receiver."},
            )

        if not attachment_files and not appendix_files:
            raise serializers.ValidationError(
                {
                    "detail": "At least one of the fields 'attachment_files' or 'appendix_files' must be provided.",
                },
            )

        # Validate file types
        for file in attachment_files:
            self.validate_file_type(file)

        for file in appendix_files:
            self.validate_file_type(file)

        return data

    def create(self, validated_data):
        attachment_files = validated_data.pop("attachment_files", [])
        appendix_files = validated_data.pop("appendix_files", [])
        receivers_pks = list(map(int, validated_data.pop("receivers_ids", []).split(',')))

        validated_data["document_code"] = uuid.uuid4()

        document = Document.objects.create(**validated_data)

        receivers = User.objects.filter(pk__in=receivers_pks)
        missing_receivers = set(receivers_pks) - set(
            receivers.values_list("pk", flat=True),
        )
        if missing_receivers:
            raise serializers.ValidationError(
                {"detail": f"Users with Pks {missing_receivers} do not exist."},
            )
        document.receivers.add(*receivers)
        DocumentReceiver.objects.filter(
            document=document,
            receiver__in=receivers,
        ).update(created_by=document.created_by)
        document.associate_assets(attachment_files, Asset.ATTACHMENT)
        document.associate_assets(appendix_files, Asset.APPENDIX)

        return document

    def to_representation(self, instance):
        request = self.context.get('request', None)
        data = super().to_representation(instance)
        if request:
            if instance.created_by.id == request.user.id:
                data["sender"] = UserSerializer(request.user).data
                data["arrival_at"] = int((float(instance.created_at.timestamp())) * 1000)
            else:
                document_receivers = instance.document_receivers.filter(receiver_id=request.user.id).first()
                data["sender"] = UserSerializer(document_receivers.created_by).data
                data["arrival_at"] = int((float(document_receivers.created_at.timestamp())) * 1000)
        attachment_files = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.ATTACHMENT,
                document_id=instance.id,
            ),
            many=True,
        ).data
        appendix_files = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.APPENDIX,
                document_id=instance.id,
            ),
            many=True,
        ).data

        data["attachment_files"] = attachment_files
        data["appendix_files"] = appendix_files
        return data
