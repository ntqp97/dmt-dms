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
from ..assets.models import Asset
from ..common.s3_helper import S3FileManager
from ..notifications.services import NotificationService
from django.core.cache import cache


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
                    self.update_signature_status(document_signature, sign_status_response, request.user)

                    return Response(status=status.HTTP_200_OK)
                else:
                    raise ValueError(f"No signer found for the transaction ID: {transaction_id}.")
        except Exception as e:
            print(e)
            return ErrorResponse(
                str(e),
            ).failure_response()

    @transaction.atomic
    def update_signature_status(self, document_signature, sign_status_response, user):
        status_mapping = {
            "1": DocumentSignature.SIGNED,
            "4001": DocumentSignature.TIMEOUT,
            "4002": DocumentSignature.REJECTED,
            "4004": DocumentSignature.FAILED,
            "50000": DocumentSignature.FAILED,
        }

        status_code = sign_status_response.get("status")

        if status_code in status_mapping:
            document_signature.update_fields(
                signature_status=status_mapping[status_code],
                updated_by=user,
            )

        if status_mapping[status_code] == DocumentSignature.SIGNED:
            cache_key = f"signature:{document_signature.document.document_code}:{document_signature.id}"
            signature_data = cache.get(cache_key)
            signature_file = Asset.objects.filter(
                file_type=Asset.SIGNATURE_FILE,
                document_id=document_signature.document.id,
            ).first()

            if signature_data and signature_file:
                signed_bytes = sign_status_response.get("signatures")[0]
                signature_data['signed_bytes'] = signed_bytes

                signature_file_input = signature_file.get_asset_file(
                    access_key=settings.AWS_ACCESS_KEY_ID,
                    secret_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME,
                    bucket_name=settings.AWS_STORAGE_BUCKET_NAME
                ).read()

                signed_pdf_data = MySignHelper.generate_signed_pdf(signature_data, signature_file_input)
                S3FileManager.upload_file_to_s3(
                    data=signed_pdf_data,
                    bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
                    s3_object_name=signature_file.file.name,
                    s3_client=S3FileManager.s3_connection(
                        settings.AWS_ACCESS_KEY_ID,
                        settings.AWS_SECRET_ACCESS_KEY,
                        settings.AWS_S3_REGION_NAME
                    ),
                    is_object=True
                )
            else:
                raise ValueError("There must be exactly 1 signature for this order.")
            next_signature = document_signature.document.signatures.filter(
                order=int(document_signature.order) + 1
            )
            if next_signature.count() > 1:
                raise ValueError("There must be exactly 1 signature for this order.")

            if next_signature.exists():
                # TODO Notify the next signer
                NotificationService.send_notification_to_users(
                    sender=user,
                    receivers=[next_signature.first().signer],
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
