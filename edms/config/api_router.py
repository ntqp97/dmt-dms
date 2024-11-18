from django.urls import include
from django.urls import path

API_PREFIX = "api/v1/"

urlpatterns = [
    path(f"{API_PREFIX}", include("edms.users.api.urls")),
    path(f"{API_PREFIX}", include("edms.organization.urls")),
    path(f"{API_PREFIX}", include("edms.documents.urls")),
    path(f"{API_PREFIX}", include("edms.assets.urls")),
    path(f"{API_PREFIX}", include("edms.meeting_schedule.urls")),
]
