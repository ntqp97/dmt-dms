import os

from rest_framework import serializers

# TODO: change to env config
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_type(file, allowed_extensions):
    _, file_extension = os.path.splitext(file.name)
    if file_extension.replace(".", "").lower() not in allowed_extensions:
        raise serializers.ValidationError(
            {"detail": f"Unsupported file type: {file_extension}."},
        )

    if file.size > MAX_FILE_SIZE:
        raise serializers.ValidationError(
            {"detail": f"File size exceeds the limit ({MAX_FILE_SIZE/(1024*1024)}MB)."}
        )

    return file
