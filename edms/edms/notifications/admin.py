from django.contrib import admin

# Register your models here.
from .models import Notification, NotificationReceiver


class NotificationReceiverInline(admin.TabularInline):
    model = NotificationReceiver
    extra = 1


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "body", "get_receivers")
    search_fields = ("title", "body", "receivers__name")
    list_filter = ("receivers__is_active",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "body",
                "data",
            )
        }),
    )

    inlines = [NotificationReceiverInline]

    def get_receivers(self, obj):
        return ", ".join([user.name for user in obj.receivers.all()])
    get_receivers.short_description = "Receivers"


@admin.register(NotificationReceiver)
class NotificationReceiverAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification",
        "receiver",
        "is_push",
        "is_read",
        "read_at",
    )
    search_fields = ("notification__title", "receiver__name")
    list_filter = ("is_push", "is_read", "read_at")
    ordering = ("-read_at",)

    fieldsets = (
        (None, {
            "fields": (
                "notification",
                "receiver",
                "is_push",
                "is_read",
                "read_at",
            )
        }),
    )
