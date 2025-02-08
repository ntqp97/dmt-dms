# Create your views here.
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edms.common.app_status import AppResponse
from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.pdf_helper import add_watermark_to_pdf
import datetime
from django.conf import settings

from edms.common.permissions import IsOwnerOrAdmin
from edms.documents.models import Document


class AssetViewSet(
    viewsets.GenericViewSet,
    mixins.DestroyModelMixin,
):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_permissions(self):
        if self.action in ["destroy"]:
            self.permission_classes = [IsOwnerOrAdmin]
        return super(self.__class__, self).get_permissions()

    def destroy(self, request, *args, **kwargs):
        asset = self.get_object()
        if asset.document and asset.document.document_category != Document.SIGNING_DOCUMENT:
            return Response(
                AppResponse.DELETE_ASSETS_FAILURE.failure_response,
                status=AppResponse.DELETE_ASSETS_FAILURE.status_code
            )

        return super().destroy(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='preview-pdf'
    )
    def get_preview_pdf(self, request, pk=None):
        asset = get_object_or_404(self.get_queryset(), id=pk)

        input_pdf = asset.get_asset_file(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
        )
        watermark_text = f"{request.user.name} - {request.user.citizen_identification} - {datetime.datetime.now().strftime('%d/%m/%Y')}"
        output_pdf = add_watermark_to_pdf(input_pdf, watermark_text, asset)

        response = HttpResponse(output_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{asset.asset_name}_watermarked.pdf"'
        return response
