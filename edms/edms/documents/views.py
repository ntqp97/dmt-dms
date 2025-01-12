import json

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edms.common.app_status import AppResponse
from edms.common.app_status import ErrorResponse
from edms.common.helper import custom_error
from edms.common.pagination import StandardResultsSetPagination
from edms.common.permissions import IsOwnerOrAdmin
from edms.documents.filters import DocumentFilter
from edms.documents.models import Document, DocumentSignature, DocumentReceiver
from edms.documents.serializers import DocumentSerializer, SendDocumentSerializer
from edms.organization.models import OrganizationUnit
from edms.search.filters import UnaccentSearchFilter
from edms.users.models import User
from django.conf import settings


# Create your views here.
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = DocumentSerializer
    filter_backends = (
        DjangoFilterBackend,
        UnaccentSearchFilter,
    )
    filterset_class = DocumentFilter
    search_fields = [
        "document_title",
        "document_summary",
        "document_number_reference_code",
    ]

    def get_permissions(self):
        if self.action in ["destroy", "update", "partial_update"]:
            self.permission_classes = [IsOwnerOrAdmin]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        # if user.is_staff or user.is_superuser:
        #     queryset = Document.objects.all()
        # else:
        queryset = Document.objects.filter(
            Q(created_by=user) | Q(receivers__in=[user]) | Q(signers__in=[user]),
        ).distinct()
        return queryset.order_by("-id")

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if document.document_category != Document.SIGNING_DOCUMENT:
            return Response(
                AppResponse.DELETE_DOCUMENTS_FAILURE.success_response,
                status=AppResponse.DELETE_DOCUMENTS_FAILURE.status_code
            )

        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def process_signers(self, signers):
        signers_list = []
        if signers:
            signers_list = (
                json.loads(signers)
                if isinstance(signers, str)
                else signers
            )
        return signers_list

    def create(self, request, *args, **kwargs):
        signers_list = self.process_signers(request.data.get("signers_flow"))
        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
                'signers_flow': signers_list
            }
        )
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        signers_list = self.process_signers(request.data.get("signers_flow"))
        if instance.document_category != Document.SIGNING_DOCUMENT:
            return Response(
                AppResponse.UPDATE_DOCUMENTS_FAILURE.success_response,
                status=AppResponse.UPDATE_DOCUMENTS_FAILURE.status_code
            )

        serializer = self.get_serializer(
            instance,
            data=request.data,
            context={
                'request': request,
                'signers_flow': signers_list
            },
            partial=True  # Sử dụng partial=True nếu chỉ cần cập nhật một số trường
        )
        if serializer.is_valid():
            self.perform_update(serializer)
            data = AppResponse.UPDATE_DOCUMENTS.success_response
            data["results"] = serializer.data
            response = Response(
                data,
                status=AppResponse.UPDATE_DOCUMENTS.status_code,
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
        user = request.user
        created_docs_count = Document.objects.filter(
            created_by=user,
            document_category__in=[
                Document.NORMAL_DOCUMENT,
                Document.COMPLETED_SIGNING_DOCUMENT,
            ]
        ).count()
        received_docs_count = (
            Document.objects.filter(
                document_receivers__receiver=user,
                document_category__in=[
                    Document.NORMAL_DOCUMENT,
                    Document.COMPLETED_SIGNING_DOCUMENT,
                ]
            )
            .distinct()
            .count()
        )
        forwarded_docs_count = (
            Document.objects.filter(
                document_receivers__created_by=user,
                document_category__in=[
                    Document.NORMAL_DOCUMENT,
                    Document.COMPLETED_SIGNING_DOCUMENT,
                ]
            ).exclude(
                document_receivers__receiver=user,
            ).distinct().count()
        )
        unread_docs_count = (
            Document.objects.filter(
                document_receivers__receiver=user,
                document_receivers__is_read=False,
                document_category__in=[
                    Document.NORMAL_DOCUMENT,
                    Document.COMPLETED_SIGNING_DOCUMENT,
                ]
            ).distinct().count()
        )
        pending_signing_docs_count = (
            Document.objects.filter(
                document_category=Document.IN_PROGRESS_SIGNING_DOCUMENT,
                signatures__signer=user,
                signatures__signature_status__in=[
                    DocumentSignature.UNSIGNED,
                    DocumentSignature.FAILED,
                    DocumentSignature.TIMEOUT,
                ],
                signatures__is_signature_visible=True
            ).distinct().count()
        )

        pending_initial_signing_docs_count = (
            Document.objects.filter(
                document_category=Document.IN_PROGRESS_SIGNING_DOCUMENT,
                signatures__signer=user,
                signatures__signature_status__in=[
                    DocumentSignature.UNSIGNED,
                    DocumentSignature.FAILED,
                    DocumentSignature.TIMEOUT,
                ],
                signatures__is_signature_visible=False
            ).distinct().count()
        )

        data = AppResponse.STATISTICS_DOCUMENTS.success_response
        data["results"] = {
            "created": created_docs_count,
            "received": received_docs_count,
            "forwarded": forwarded_docs_count,
            "unread": unread_docs_count,
            "pending_signing": pending_signing_docs_count,
            "pending_initial_signing": pending_initial_signing_docs_count,
        }
        return Response(data, status=AppResponse.STATISTICS_DOCUMENTS.status_code)

    @action(
        methods=["PUT"],
        detail=True,
        permission_classes=[IsAuthenticated],
        serializer_class=None,
        url_path="mark-as-read"
    )
    def mark_as_read(self, request, pk=None):
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
            document_receiver = DocumentReceiver.objects.get(
                document=document,
                receiver=request.user
            )
        except DocumentReceiver.DoesNotExist:
            return Response({"detail": "DocumentReceiver not found."}, status=status.HTTP_404_NOT_FOUND)

        if document_receiver.is_read:
            return Response({"detail": "Document already marked as read."}, status=status.HTTP_400_BAD_REQUEST)

        document_receiver.mark_as_read()
        return Response({"detail": "Document marked as read."}, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        serializer_class=SendDocumentSerializer,
        url_name='send-document',
        url_path="send"
    )
    def send(self, request, pk=None):
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
            serializer = SendDocumentSerializer(
                data=request.data,
                context={
                    'document': document,
                    'request': request,
                }
            )
            if serializer.is_valid():
                recipient_type = serializer.validated_data['recipient_type']
                recipient_ids = list(map(int, serializer.validated_data.get("recipient_id", []).split(',')))
                if recipient_type == 'user':
                    receivers = User.objects.filter(id__in=recipient_ids)
                    document.send_to_users(sender=request.user, receivers=receivers)
                    return Response(
                        {"message": f"Document sent successfully!"},
                        status=AppResponse.SEND_DOCUMENTS.status_code
                    )

                elif recipient_type == 'organization':
                    organizations = OrganizationUnit.objects.filter(id__in=recipient_ids)
                    document_receivers = document.send_to_organizations(sender=request.user, organizations=organizations)
                    return Response(
                        {
                            "message": f"Document sent to {len(document_receivers)} users in organization successfully!"
                        },
                        status=AppResponse.SEND_DOCUMENTS.status_code
                    )
            else:
                return ErrorResponse(
                    custom_error("DOCUMENT", serializer.errors),
                ).failure_response()
        except ValueError as e:
            return ErrorResponse(
                str(e),
            ).failure_response()

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        serializer_class=None,
        url_name='start-signing-document',
        url_path="start-sign"
    )
    def start_signing_document(self, request, pk=None):
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
            document.start_sign(request=request)
            return Response(
                data=AppResponse.START_SIGNING_DOCUMENTS.success_response,
                status=AppResponse.START_SIGNING_DOCUMENTS.status_code
            )
        except ValueError as e:
            return ErrorResponse(
                str(e),
            ).failure_response()

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        serializer_class=None,
        url_name='signing-document',
        url_path="sign"
    )
    def signing_document(self, request, pk=None):
        try:
            document = get_object_or_404(self.get_queryset(), id=pk)
            sign_hash_response = document.sign(
                request=request,
                client_id=settings.MS_CLIENT_ID,
                client_secret=settings.MS_CLIENT_SECRET,
                base_url=settings.MS_BASE_URL,
                profile_id=settings.MS_PROFILE_ID,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
            )
            data = AppResponse.START_SIGNING_DOCUMENTS.success_response
            data["transaction_id"] = sign_hash_response.get("transactionId")
            return Response(
                data=data,
                status=AppResponse.START_SIGNING_DOCUMENTS.status_code
            )
        except ValueError as e:
            return ErrorResponse(
                str(e),
            ).failure_response()
