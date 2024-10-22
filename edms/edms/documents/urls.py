from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from edms.documents.signing_views import MySignClientAuthenticateAPIView, WebhookMySignAPIView
from edms.documents.views import DocumentViewSet

router = DefaultRouter()
router.register(r"documents", DocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("mysign/authenticate/", MySignClientAuthenticateAPIView.as_view(), name='authenticate'),
    path("mysign/signing-webhook/", WebhookMySignAPIView.as_view(), name='signing-webhook'),
]
