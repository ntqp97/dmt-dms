from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        created_by = getattr(obj, "created_by", None)
        return request.user and (
            request.user.is_staff
            or obj == request.user
            or (created_by and created_by == request.user)
        )
