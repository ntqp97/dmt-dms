from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from edms.documents.views import DocumentViewSet

router = DefaultRouter()
router.register(r"documents", DocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
