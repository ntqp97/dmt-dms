from django.contrib import admin

# Register your models here.
from .models import MeetingSchedule


@admin.register(MeetingSchedule)
class MeetingScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room_name",
        "meeting_topic",
        "start_time",
        "end_time",
        "status",
    )
    list_filter = ("status", "start_time", "end_time")
    search_fields = ("room_name", "meeting_topic", "user_contact__name", "user_host__name")
    ordering = ("-start_time",)
    filter_horizontal = ("participants",)
    fieldsets = (
        (None, {
            "fields": (
                "room_name",
                "meeting_topic",
                "dress_code",
                "meeting_content",
                "note",
            ),
        }),
        ("User Information", {
            "fields": (
                "user_contact",
                "user_host",
                "participants",
                "other_participants",
            ),
        }),
        ("Schedule Details", {
            "fields": (
                "start_time",
                "end_time",
                "status",
            ),
        }),
    )
