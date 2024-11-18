from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from edms.meeting_schedule.views import MeetingScheduleViewSet

router = DefaultRouter()
router.register(r"meeting_schedule", MeetingScheduleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
