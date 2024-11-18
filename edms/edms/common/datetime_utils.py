from datetime import datetime, timezone


def timestamp_to_datetime_ms(timestamp: int) -> datetime:
    """
    Converts a timestamp in milliseconds (ms since epoch) to a UTC datetime object.

    Args:
        timestamp (int): The timestamp in milliseconds.

    Returns:
        datetime: A datetime object in UTC.
    """
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def datetime_to_timestamp_ms(dt: datetime) -> int:
    """
    Converts a datetime object to a timestamp in milliseconds (ms since epoch).

    Args:
        dt (datetime): A datetime object. Must include tzinfo.

    Returns:
        int: The timestamp in milliseconds.

    Raises:
        ValueError: If the datetime object does not have timezone information.
    """
    if dt.tzinfo is None:
        raise ValueError("The datetime object must have timezone information (tzinfo).")
    return int(dt.timestamp() * 1000)
