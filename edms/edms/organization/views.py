from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import OrganizationUnit
from .serializers import OrganizationUnitSerializer
from .serializers import OrganizationUnitTreeSerializer


class OrganizationUnitViewSet(viewsets.ModelViewSet):
    model = OrganizationUnit
    queryset = OrganizationUnit.objects.all()
    serializer_class = OrganizationUnitSerializer

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAdminUser]
        return super(self.__class__, self).get_permissions()

    @action(
        detail=False,
        url_path="tree",
    )
    def get_organization_unit_tree(self, request):
        root_units = OrganizationUnit.objects.filter(parent__isnull=True)
        serializer = OrganizationUnitTreeSerializer(
            root_units,
            many=True,
            context={
                'request': request,
            },
        )
        return Response(serializer.data)
