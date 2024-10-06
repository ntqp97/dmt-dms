# Create your views here.
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

import config
from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.pdf_helper import add_watermark_to_pdf
from django.conf import settings
from edms.common.s3_helper import S3FileManager


class AssetViewSet(viewsets.GenericViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    @action(detail=True, methods=['get'], url_path='preview-pdf')
    def get_preview_pdf(self, request, pk=None):
        asset = get_object_or_404(self.get_queryset(), id=pk)

        s3_client = S3FileManager.s3_connection(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        input_pdf = S3FileManager.get_pdf_from_s3(
            bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
            file_key=asset.file.name,
            s3_client=s3_client
        )
        output_pdf = add_watermark_to_pdf(input_pdf, request.user.name, asset.file_type)

        response = HttpResponse(output_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{asset.asset_name}_watermarked.pdf"'
        return response
