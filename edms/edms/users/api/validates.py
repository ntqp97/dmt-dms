from rest_framework import serializers


def validate_user(user):
    if not user:
        raise serializers.ValidationError({"detail": "user incorrect"})
    if not user.is_active:
        raise serializers.ValidationError({"detail": "user not active"})
