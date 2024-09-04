from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edms.common.app_status import AppResponse
from edms.common.app_status import ErrorResponse
from edms.common.helper import custom_error
from edms.common.pagination import StandardResultsSetPagination
from edms.common.permissions import IsOwnerOrAdmin
from edms.documents.models import Document
from edms.documents.serializers import DocumentSerializer


# Create your views here.
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = DocumentSerializer

    def get_permissions(self):
        if self.action in ["destroy", "update", "partial_update"]:
            self.permission_classes = [IsOwnerOrAdmin]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            queryset = Document.objects.all()
        else:
            queryset = Document.objects.filter(
                Q(created_by=user) | Q(receivers=user),
            )
        return queryset.order_by("-id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            data = AppResponse.CREATE_DOCUMENTS.success_response
            data["results"] = serializer.data
            response = Response(
                data,
                status=AppResponse.CREATE_DOCUMENTS.status_code,
            )
        else:
            response = ErrorResponse(
                custom_error("DOCUMENT", serializer.errors),
            ).failure_response()
        return response

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="statistics",
    )
    def statistics(self, request):
        user = self.request.user
        created_docs_count = Document.objects.filter(created_by=user).count()
        sent_docs_count = (
            Document.objects.filter(
                document_receivers__created_by=user,
            )
            .exclude(
                document_receivers__receiver=user,
            )
            .distinct()
            .count()
        )

        received_docs_count = (
            Document.objects.filter(document_receivers__receiver=user)
            .distinct()
            .count()
        )
        read_docs_count = (
            Document.objects.filter(
                document_receivers__receiver=user,
                document_receivers__is_read=True,
            )
            .distinct()
            .count()
        )
        unread_docs_count = (
            Document.objects.filter(
                document_receivers__receiver=user,
                document_receivers__is_read=False,
            )
            .distinct()
            .count()
        )

        data = AppResponse.STATISTICS_DOCUMENTS.success_response
        data["results"] = {
            "created_docs": created_docs_count,
            "sent_docs": sent_docs_count,
            "received_docs": received_docs_count,
            "read_docs": read_docs_count,
            "unread_docs": unread_docs_count,
        }
        return Response(data, status=AppResponse.STATISTICS_DOCUMENTS.status_code)

    # @action(
    #     methods=["put"],
    #     detail=True,
    #     permission_classes=[IsAuthenticated],
    #     serializer_class=MarkAsReadSerializer,
    #     url_path="mark-as-read"
    # )
    # def mark_as_read(self, request, pk=None):
    #     try:
    #         obj = get_object_or_404(self.get_queryset(), id=pk)
    #         document_receiver = DocumentReceiver.objects.get(document_id=pk, receiver=request.user)
    #     except DocumentReceiver.DoesNotExist:
    #         return Response({"detail": "DocumentReceiver not found."}, status=status.HTTP_404_NOT_FOUND)
    #
    #     if document_receiver.is_read:
    #         return Response({"detail": "Document already marked as read."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     serializer = MarkAsReadSerializer(document_receiver, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({"detail": "Document marked as read."}, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
