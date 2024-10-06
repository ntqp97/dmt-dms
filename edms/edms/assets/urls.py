from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from edms.assets.views import AssetViewSet

router = DefaultRouter()
router.register(r"assets", AssetViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
