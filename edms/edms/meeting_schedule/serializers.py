import logging
from rest_framework import serializers

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.custom_fields import TimestampToDatetimeField
from edms.common.upload_helper import validate_file_type
from edms.meeting_schedule.models import MeetingSchedule
from edms.notifications.services import NotificationService
from edms.users.api.serializers import UserSerializer

logger = logging.getLogger(__name__)


class BaseMeetingScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = MeetingSchedule
        fields = [
            "id", "room_name", "meeting_topic", "dress_code",
            "meeting_content", "note", "other_participants",
            "start_time", "end_time", "status",
        ]


class ReviewMeetingScheduleSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=MeetingSchedule.MEETING_SCHEDULE_STATUS)
    note = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        try:
            instance.update_status(validated_data.get('status', instance.status), user)
        except Exception as e:
            logger.error("Error: %s", e)
            raise serializers.ValidationError({"detail": str(e)})
        instance.note = validated_data.get('note', instance.note)
        instance.updated_by = validated_data.get('updated_by', instance.updated_by)
        instance.save()

        if instance.status == MeetingSchedule.APPROVED:
            receivers = list(set([instance.user_contact, instance.user_host] + list(instance.participants.all())))
            NotificationService.send_notification_to_users(
                sender=instance.updated_by,
                receivers=receivers,
                title="Lịch họp đã được phê duyệt",
                body=f"Lịch họp với topic '{instance.meeting_topic}' đã được phê duyệt.",
                image=None,
                data={
                    "meeting_schedule_id": str(instance.id)
                }
            )
        if instance.status == MeetingSchedule.CANCELLED:
            receivers = list(set([instance.user_contact, instance.user_host] + list(instance.participants.all())))
            NotificationService.send_notification_to_users(
                sender=instance.updated_by,
                receivers=receivers,
                title="Lịch họp đã bị huỷ",
                body=f"Lịch họp với topic '{instance.meeting_topic}' đã bị huỷ.",
                image=None,
                data={
                    "meeting_schedule_id": str(instance.id)
                }
            )

        if instance.status == MeetingSchedule.REJECTED:
            receivers = [instance.created_by]
            NotificationService.send_notification_to_users(
                sender=instance.updated_by,
                receivers=receivers,
                title="Lịch họp của bạn không được phê duyệt",
                body=f"Lịch họp với topic '{instance.meeting_topic}' không được phê duyệt.",
                image=None,
                data={
                    "meeting_schedule_id": str(instance.id)
                }
            )
        return instance


class MeetingScheduleSerializer(serializers.ModelSerializer):
    attachment_files = serializers.ListField(
        required=False,
        child=serializers.FileField(),
    )

    user_contact_id = serializers.CharField(
        required=True,
        write_only=True,
    )
    user_contact = UserSerializer(
        read_only=True,
    )

    user_host_id = serializers.CharField(
        required=True,
        write_only=True,
    )
    user_host = UserSerializer(
        read_only=True,
    )

    participants_ids = serializers.CharField(
        required=False,
        write_only=True,
    )
    participants = UserSerializer(
        many=True,
        read_only=True,
    )

    start_time = TimestampToDatetimeField(required=True)
    end_time = TimestampToDatetimeField(required=True)

    class Meta:
        model = MeetingSchedule
        fields = [
            "id",
            "room_name",
            "meeting_topic",
            "dress_code",
            "meeting_content",
            "note",
            "user_contact_id",
            "user_contact",
            "user_host_id",
            "user_host",
            "participants_ids",
            "participants",
            "other_participants",
            "start_time",
            "end_time",
            "status",
            "attachment_files",
        ]

    def validate(self, data):
        attachment_files = data.get("attachment_files", [])
        participants_ids = data.get("participants_ids", [])
        user_contact_id = data.get("user_contact_id")
        user_host_id = data.get("user_host_id")

        try:
            participants_ids = list(map(int, participants_ids.split(','))) if participants_ids else []
        except ValueError:
            raise serializers.ValidationError({"detail": "participants_ids must be a comma-separated list of integers."})

        if user_contact_id:
            try:
                user_contact_id = int(user_contact_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"detail": "user_contact_id must be an integer."})
        if user_host_id:
            try:
                user_host_id = int(user_host_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"detail": "user_host_id must be an integer."})

        for file in attachment_files:
            allowed_extensions = ["pdf", "doc", "docx"]
            validate_file_type(file, allowed_extensions)
        data["participants_ids"] = participants_ids
        data["user_contact_id"] = user_contact_id
        data["user_host_id"] = user_host_id
        return data

    def create(self, validated_data):
        attachment_files = validated_data.pop("attachment_files", [])
        participants_ids = validated_data.pop("participants_ids", [])

        meeting_schedule = MeetingSchedule.objects.create(**validated_data)
        meeting_schedule.participants.set(participants_ids)
        meeting_schedule.associate_assets(attachment_files, Asset.ATTACHMENT)
        return meeting_schedule

    def update(self, instance, validated_data):
        attachment_files = validated_data.pop("attachment_files", [])
        participants_ids = validated_data.pop("participants_ids", [])
        user_contact_id = validated_data.pop("user_contact_id", None)
        user_host_id = validated_data.pop("user_host_id", None)
        _ = validated_data.pop("status", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.user_contact_id = user_contact_id if user_contact_id else instance.user_contact_id
        instance.user_host_id = user_host_id if user_host_id else instance.user_host_id
        instance.save()
        if participants_ids:
            instance.participants.set(participants_ids)
        instance.associate_assets(attachment_files, Asset.ATTACHMENT)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["attachment_files"] = AssetSerializer(
            Asset.objects.filter(
                file_type=Asset.ATTACHMENT,
                meeting_schedule_id=instance.id,
            ),
            many=True,
            context=self.context
        ).data
        return data
