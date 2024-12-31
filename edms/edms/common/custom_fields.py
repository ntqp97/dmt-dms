from rest_framework import serializers

from edms.common.datetime_utils import datetime_to_timestamp_ms, timestamp_to_datetime_ms


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
