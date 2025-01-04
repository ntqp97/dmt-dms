# Register your models here.
from django.contrib import admin
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asset_name",
        "file_type",
        "size",
        "mime_type",
        "document",
        "meeting_schedule",
        "file",
        "created_at"
    )
    list_filter = ("file_type", "mime_type")
    search_fields = ("asset_name", "mime_type")
    readonly_fields = ("size",)
    ordering = ("-id",)
    fieldsets = (
        (None, {
            "fields": (
                "asset_name",
                "file_type",
                "file",
                "size",
                "mime_type",
            )
        }),
        ("Related Models", {
            "fields": (
                "document",
                "meeting_schedule",
            )
        }),
    )
