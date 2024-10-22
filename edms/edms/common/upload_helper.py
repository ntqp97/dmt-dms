import os

from rest_framework import serializers


def validate_file_type(file, allowed_extensions):
    _, file_extension = os.path.splitext(file.name)
    if file_extension.replace(".", "").lower() not in allowed_extensions:
        raise serializers.ValidationError(
            {"detail": f"Unsupported file type: {file_extension}."},
        )
    return file
