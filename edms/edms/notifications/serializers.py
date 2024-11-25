from rest_framework import serializers

from edms.notifications.models import Notification
from edms.users.api.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    receivers = UserSerializer(
        many=True,
        read_only=True,
    )

    sender = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Notification
        fields = ["id", "title", "body", "sender", "receivers"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["sender"] = UserSerializer(
            instance.created_by,
            context=self.context
        ).data
        return data
