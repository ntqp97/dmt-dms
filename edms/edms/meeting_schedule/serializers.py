import logging
import os
import uuid

from django.utils import timezone
from rest_framework import serializers

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.datetime_utils import timestamp_to_datetime_ms, datetime_to_timestamp_ms
from edms.common.upload_helper import validate_file_type
from edms.meeting_schedule.models import MeetingSchedule
from edms.notifications.services import NotificationService
from edms.users.api.serializers import UserSerializer

myapp_logger = logging.getLogger("django")


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
        instance.status = validated_data.get('status', instance.status)
        instance.note = validated_data.get('note', instance.note)
        instance.updated_by = validated_data.get('updated_by', instance.updated_by)
        instance.save()
        if instance.status == MeetingSchedule.APPROVED:
            receivers = list(set([instance.user_contact, instance.user_host] + list(instance.participants.all())))
            NotificationService.send_notification_to_users(
                sender=instance.updated_by,
                receivers=receivers,
                title="Lịch họp mới đã được đặt",
                body=f"Lịch họp với topic '{instance.meeting_topic}' đã được đặt.",
                image=None,
                data={
                    "meeting_schedule_id": str(instance.id)
                }
            )
        return instance


class TimestampToDatetimeField(serializers.Field):
    """
    Custom serializer field to convert timestamp (in milliseconds) to datetime and vice versa.
    """

    def to_representation(self, value):
        """
        Converts datetime to timestamp (integer).
        """
        if value is None:
            return None

        return datetime_to_timestamp_ms(value)

    def to_internal_value(self, data):
        """
        Converts timestamp (integer) to datetime.
        """
        try:
            timestamp = int(data)
        except ValueError:
            raise serializers.ValidationError("Invalid timestamp value.")

        if len(str(timestamp)) != 13:
            raise serializers.ValidationError("Timestamp should be in milliseconds.")

        return timestamp_to_datetime_ms(timestamp)


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
            raise serializers.ValidationError("participants_ids must be a comma-separated list of integers.")

        try:
            user_contact_id = int(user_contact_id)
        except (TypeError, ValueError):
            raise serializers.ValidationError("user_contact_id must be an integer.")

        try:
            user_host_id = int(user_host_id)
        except (TypeError, ValueError):
            raise serializers.ValidationError("user_host_id must be an integer.")

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
