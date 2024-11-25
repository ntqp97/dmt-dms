from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edms.common.pagination import StandardResultsSetPagination
from edms.notifications.filters import NotificationFilter
from edms.notifications.models import Notification, NotificationReceiver
from edms.notifications.serializers import NotificationSerializer


# Create your views here.
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (
        DjangoFilterBackend,
    )
    filterset_class = NotificationFilter

    http_method_names = ["get", "list", "put"]

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        queryset = Notification.objects.filter(receivers__in=[user]).distinct()
        return queryset.order_by("-id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(
        methods=["PUT"],
        detail=True,
        permission_classes=[IsAuthenticated],
        serializer_class=None,
        url_path="mark-as-read"
    )
    def mark_as_read(self, request, pk=None):
        try:
            notification = get_object_or_404(self.get_queryset(), id=pk)
            notification_receiver = NotificationReceiver.objects.get(
                notification=notification,
                receiver=request.user
            )
        except NotificationReceiver.DoesNotExist:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

        if notification_receiver.is_read:
            return Response({"detail": "Notification already marked as read."}, status=status.HTTP_400_BAD_REQUEST)

        notification_receiver.mark_as_read()
        return Response({"detail": "Notification marked as read."}, status=status.HTTP_200_OK)
