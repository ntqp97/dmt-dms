from django.contrib import admin

# Register your models here.
from .models import Option


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "description_short")
    search_fields = ("name", "type")
    list_filter = ("type",)
    ordering = ("name",)
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "description",
                "type",
            )
        }),
    )

    def description_short(self, obj):
        return obj.description[:50] + "..." if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"
