from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

from edms.notifications.views import NotificationViewSet

router = DefaultRouter()
router.register(r"devices", FCMDeviceAuthorizedViewSet)
router.register(r"notifications", NotificationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
