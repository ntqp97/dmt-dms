from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest


class SoftDeleteModelAdmin(admin.ModelAdmin):
    """Soft Delete Model Admin"""

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        queryset.update(deleted=True)

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).filter(deleted=False)
