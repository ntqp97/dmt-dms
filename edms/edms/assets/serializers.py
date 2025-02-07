from rest_framework import serializers

from edms.assets.models import Asset
from edms.documents.models import Document


class AssetSerializer(serializers.ModelSerializer):
    preview_file_url = serializers.SerializerMethodField()
    file_url_type = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "size", "mime_type", "asset_name", "file_type", "preview_file_url", "file_url_type"]
        read_only_fields = ["id", "size", "mime_type", "asset_name", "preview_file_url", "file_url_type"]

    def get_preview_file_url(self, obj):
        request = self.context.get('request')
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        if obj.file and obj.mime_type == "application/pdf":
            if obj.document and obj.document.document_category in [Document.COMPLETED_SIGNING_DOCUMENT]:
                if obj.document.security_type.lower() == "confidential":
                    return f"{scheme}://{host}/api/v1/assets/{obj.id}/preview-pdf/"
                return obj.file.url
            return f"{scheme}://{host}/api/v1/assets/{obj.id}/preview-pdf/"
        return obj.file.url

    def get_file_url_type(self, obj):
        if obj.document and obj.document.document_category in [Document.COMPLETED_SIGNING_DOCUMENT]:
            return "s3"
        if obj.file and obj.mime_type == "application/pdf":
            return "preview"
        return "s3"
