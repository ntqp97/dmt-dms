# Register your models here.
from django.contrib import admin
from .models import OrganizationUnit


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit_type", "level", "parent_name")
    search_fields = ("name", "unit_type")
    list_filter = ("unit_type", "level")
    ordering = ("level", "name")
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "parent",
                "unit_type",
                "level",
            )
        }),
    )

    def parent_name(self, obj):
        """Hiển thị tên của đơn vị cha."""
        return obj.parent.name if obj.parent else "None"
    parent_name.short_description = "Parent Unit"
