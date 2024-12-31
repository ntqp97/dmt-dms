from rest_framework import serializers

from edms.notifications.models import Notification
from edms.users.api.serializers import UserSerializer
from edms.common.custom_fields import TimestampToDatetimeField


class NotificationSerializer(serializers.ModelSerializer):
    receivers = UserSerializer(
        many=True,
        read_only=True,
    )

    sender = UserSerializer(
        read_only=True,
    )

    created_at = TimestampToDatetimeField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "title", "body", "sender", "receivers", "data", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["sender"] = UserSerializer(
            instance.created_by,
            context=self.context
        ).data
        return data
