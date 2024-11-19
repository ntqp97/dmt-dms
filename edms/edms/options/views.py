from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from edms.common.permissions import IsOwnerOrAdmin
from edms.options.filters import OptionFilter
from edms.options.models import Option
from edms.options.serializers import OptionSerializer


# Create your views here.
class OptionViewSet(viewsets.ModelViewSet):
    model = Option
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    filter_backends = (
        DjangoFilterBackend,
    )
    filterset_class = OptionFilter

    def get_permissions(self):
        if self.action in ["create", "destroy", "update", "partial_update"]:
            self.permission_classes = [IsAdminUser]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
