from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from edms.options.views import OptionViewSet

router = DefaultRouter()
router.register(r"options", OptionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
