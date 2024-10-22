from rest_framework import serializers


class MySignClientAuthenticateSerializer(serializers.Serializer):
    access_token = serializers.CharField(read_only=True)
    token_type = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)


class WebhookMySignRequestSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(write_only=True)
