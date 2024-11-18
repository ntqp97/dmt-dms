from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edms.common.app_status import AppResponse
from edms.common.app_status import ErrorResponse
from edms.common.helper import custom_error
from edms.common.pagination import StandardResultsSetPagination
from edms.common.permissions import IsOwnerOrAdmin
from edms.meeting_schedule.filters import MeetingScheduleFilter
from edms.meeting_schedule.models import MeetingSchedule
from edms.meeting_schedule.serializers import MeetingScheduleSerializer, ReviewMeetingScheduleSerializer
from edms.search.filters import UnaccentSearchFilter


# Create your views here.
class MeetingScheduleViewSet(viewsets.ModelViewSet):
    queryset = MeetingSchedule.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = MeetingScheduleSerializer
    filter_backends = (
        DjangoFilterBackend,
        UnaccentSearchFilter,
    )
    filterset_class = MeetingScheduleFilter
    search_fields = [
        "room_name",
        "meeting_topic",
        "meeting_content",
    ]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action in ["destroy", "update", "partial_update"]:
            self.permission_classes = [IsOwnerOrAdmin]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            queryset = MeetingSchedule.objects.all()
        else:
            queryset = MeetingSchedule.objects.filter(
                Q(created_by=user) |
                Q(user_contact=user) |
                Q(user_host=user) |
                Q(participants__in=[user])
            ).distinct()
            queryset = queryset.filter(
                Q(status=MeetingSchedule.APPROVED) |
                Q(status=MeetingSchedule.CANCELLED) |
                Q(created_by=user)
            )
        return queryset.order_by("-id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
            }
        )

        if serializer.is_valid():
            self.perform_create(serializer)
            data = AppResponse.CREATE_MEETING_SCHEDULE.success_response
            data["results"] = serializer.data
            response = Response(
                data,
                status=AppResponse.CREATE_DOCUMENTS.status_code,
            )
        else:
            response = ErrorResponse(
                custom_error("MEETING_SCHEDULE", serializer.errors),
            ).failure_response()
        return response

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsOwnerOrAdmin],
        serializer_class=ReviewMeetingScheduleSerializer,
        url_name="review-meeting-schedule",
        url_path="review"
    )
    def review(self, request, pk=None):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = ReviewMeetingScheduleSerializer(
            instance,
            data=request.data,
            context={
                'request': request,
            }
        )

        if serializer.is_valid():
            self.perform_update(serializer)
            data = AppResponse.UPDATE_MEETING_SCHEDULE.success_response
            return Response(data, status=AppResponse.UPDATE_MEETING_SCHEDULE.status_code)
        else:
            return ErrorResponse(
                custom_error("MEETING_SCHEDULE", serializer.errors)
            ).failure_response()
