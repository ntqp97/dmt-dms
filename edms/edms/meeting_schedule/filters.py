import django_filters
from .models import MeetingSchedule
from edms.search.filters import UnaccentFilter, NumberInFilter


class MeetingScheduleFilter(django_filters.FilterSet):
    room_name = UnaccentFilter(field_name='room_name')
    meeting_topic = UnaccentFilter(field_name='meeting_topic')
    dress_code = UnaccentFilter(field_name='dress_code')
    meeting_content = UnaccentFilter(field_name='meeting_content')
    note = UnaccentFilter(field_name='note')
    other_participants = UnaccentFilter(field_name='other_participants')
    status = django_filters.CharFilter(lookup_expr='exact')

    start_time = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()

    participants = NumberInFilter(
        field_name='participants__id',
        lookup_expr='in',
        distinct=True,
    )

    class Meta:
        model = MeetingSchedule
        fields = [
            "room_name",
            "meeting_topic",
            "dress_code",
            "meeting_content",
            "note",
            "participants",
            "other_participants",
            "start_time",
            "status",
            "created_at",
        ]
