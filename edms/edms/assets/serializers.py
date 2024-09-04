from rest_framework import serializers

from edms.assets.models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["id", "file", "size", "mime_type", "asset_name", "file_type"]
        read_only_fields = ["id", "size", "mime_type", "asset_name"]

    # def create(self, validated_data):
    #     file_instance = validated_data.get('file')
    #     validated_data['size'] = file_instance.size
    #     validated_data['name'] = file_instance.name
    #     validated_data['mime_type'] = mimetypes.guess_type(file_instance.name)[0]
    #     return super().create(validated_data)
