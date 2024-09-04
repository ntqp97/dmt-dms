from rest_framework import serializers

from edms.organization.models import OrganizationUnit
from edms.users.api.serializers import UserSerializer


class OrganizationUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUnit
        fields = ["id", "name", "level", "users", "parent"]
        read_only_fields = ["id", "users"]


class OrganizationUnitTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    users = UserSerializer(many=True)

    class Meta:
        model = OrganizationUnit
        fields = ["id", "name", "level", "children", "users"]

    def get_children(self, obj):
        return OrganizationUnitTreeSerializer(obj.get_children(), many=True).data
