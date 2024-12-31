from rest_framework import serializers

from edms.assets.models import Asset
from edms.documents.models import Document


class AssetSerializer(serializers.ModelSerializer):
    preview_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "size", "mime_type", "asset_name", "file_type", "preview_file_url"]
        read_only_fields = ["id", "size", "mime_type", "asset_name", "preview_file_url"]

    def get_preview_file_url(self, obj):
        request = self.context.get('request')
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        if obj.document and obj.document.document_category in [Document.COMPLETED_SIGNING_DOCUMENT]:
            return obj.file.url
        if obj.file and obj.mime_type == "application/pdf":
            return f"{scheme}://{host}/api/v1/assets/{obj.id}/preview-pdf/"
        return obj.file.url
