from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import DocumentSignature, Document
from .signing_utils import MySignHelper
from .sigining_serializers import MySignClientAuthenticateSerializer, WebhookMySignRequestSerializer
from django.conf import settings
from edms.common.app_status import ErrorResponse
from ..notifications.services import NotificationService


class WebhookMySignAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookMySignRequestSerializer

    def post(self, request):
        try:
            serializer = WebhookMySignRequestSerializer(data=request.data)
            if serializer.is_valid():
                transaction_id = serializer.validated_data["transaction_id"]
                print("transaction_id", transaction_id)
                print("User", request.user)
                document_signature = DocumentSignature.objects.get(transaction_id=transaction_id)
                print("document_signature", document_signature.id)
                if document_signature:
                    access_token = MySignHelper.login(
                        user_id=request.user.external_user_id,
                        base_url=settings.MS_BASE_URL,
                        client_id=settings.MS_CLIENT_ID,
                        client_secret=settings.MS_CLIENT_SECRET,
                        profile_id=settings.MS_PROFILE_ID,
                    )["access_token"]

                    sign_status_response = MySignHelper.get_sign_status(
                        access_token=access_token,
                        base_url=settings.MS_BASE_URL,
                        transaction_id=transaction_id
                    )
                    self.update_signature_status(document_signature, sign_status_response.get("status"), request.user)

                    return Response(status=status.HTTP_200_OK)
                else:
                    raise ValueError(f"No signer found for the transaction ID: {transaction_id}.")
        except Exception as e:
            print(e)
            return ErrorResponse(
                str(e),
            ).failure_response()

    @transaction.atomic
    def update_signature_status(self, document_signature, status_code, user):
        status_mapping = {
            "1": DocumentSignature.SIGNED,
            "4001": DocumentSignature.TIMEOUT,
            "4002": DocumentSignature.REJECTED,
            "4004": DocumentSignature.FAILED,
            "50000": DocumentSignature.FAILED,
        }

        if status_code in status_mapping:
            document_signature.update_fields(
                signature_status=status_mapping[status_code],
                updated_by=user,
            )

        if status_mapping[status_code] == DocumentSignature.SIGNED:
            next_signature = document_signature.document.signatures.filter(
                order=int(document_signature.order) + 1
            )
            if next_signature.count() > 1:
                raise ValueError("There must be exactly 1 signature for this order.")

            if next_signature.exists():
                # TODO Notify the next signer
                NotificationService.send_notification_to_users(
                    sender=user,
                    receivers=[next_signature.signer],
                    title="Yêu cầu ký tài liệu",
                    body=f"Tài liệu {document_signature.document.document_title} cần được ký. Vui lòng kiểm tra và hoàn tất.",
                    image=None,
                    data={
                        "document_id": str(document_signature.document.id)
                    }
                )
            else:
                document_signature.document.update_fields(
                    document_category=Document.COMPLETED_SIGNING_DOCUMENT,
                    updated_by=user,
                )
                NotificationService.send_notification_to_users(
                    sender=user,
                    receivers=list(set([signature.signer for signature in document_signature.document.signatures.all()])),
                    title="Tài liệu đã trình ký thành công",
                    body=f"Tài liệu {document_signature.document.document_title} đã trình ký thành công.",
                    image=None,
                    data={
                        "document_id": str(document_signature.document.id)
                    }
                )


class MySignClientAuthenticateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MySignClientAuthenticateSerializer

    def post(self, request):
        response = MySignHelper.client_authenticate(
            base_url=settings.MS_BASE_URL,
            client_id=settings.MS_CLIENT_ID,
            client_secret=settings.MS_CLIENT_SECRET,
        )
        if not response:
            return ErrorResponse(str("Authentication with MySign failed."),).failure_response()

        if response.status_code != 200:
            return Response(data=response.json(), status=status.HTTP_400_BAD_REQUEST)

        return Response(data=response.json(), status=status.HTTP_200_OK)
