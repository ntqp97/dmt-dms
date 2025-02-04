import logging

from django.db import models

from edms.assets.models import Asset
from edms.common.basemodels import BaseModel
from edms.core.models import SoftDeleteModel
import mimetypes

logger = logging.getLogger(__name__)

# Create your models here.
class MeetingSchedule(SoftDeleteModel, BaseModel):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    MEETING_SCHEDULE_STATUS = [
        (PENDING_APPROVAL, PENDING_APPROVAL),
        (APPROVED, APPROVED),
        (REJECTED, REJECTED),
        (CANCELLED, CANCELLED),
    ]

    _admin_allowed_transitions = {
        PENDING_APPROVAL: {APPROVED, REJECTED},
        APPROVED: {CANCELLED},
        REJECTED: set(),
        CANCELLED: set()
    }

    _owner_allowed_transitions = {
        PENDING_APPROVAL: set(),
        APPROVED: {CANCELLED},
        REJECTED: set(),
        CANCELLED: set()
    }

    room_name = models.CharField(max_length=255, blank=True, null=True)
    meeting_topic = models.CharField(max_length=500, blank=True, null=True)
    dress_code = models.CharField(max_length=255, blank=True, null=True)
    meeting_content = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    user_contact = models.ForeignKey(
        'users.User',
        related_name='user_contact',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    user_host = models.ForeignKey(
        'users.User',
        related_name='user_host',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    participants = models.ManyToManyField(
        'users.User',
        related_name='participants',
        blank=True
    )
    other_participants = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=MEETING_SCHEDULE_STATUS,
        default=PENDING_APPROVAL,
    )

    def associate_assets(self, files, file_type):
        Asset.objects.bulk_create(
            [
                Asset(
                    meeting_schedule=self,
                    file_type=file_type,
                    file=file,
                    size=file.size,
                    asset_name=file.name,
                    mime_type=(
                        mimetypes.guess_type(file.name)[0]
                        if mimetypes.guess_type(file.name)[0]
                        else file.content_type
                    ),
                    created_by=self.created_by,
                )
                for file in files
            ],
        )

    def update_status(self, new_status, user):
        """
        Update the meeting status based on the user's role and allowed transitions.

        - Admin can change:
          * PENDING_APPROVAL -> APPROVED or REJECTED
          * APPROVED -> CANCELLED

        - Owner can change:
          * APPROVED -> CANCELLED

        Parameters:
            new_status (str): The new status to update to.
            user (User): The user attempting the status update.

        Raises:
            Exception: If the transition is not allowed based on the current status and user role.
        """
        if user.is_staff or user.is_superuser:
            allowed = self._admin_allowed_transitions.get(self.status, set())
        elif self.created_by == user:
            allowed = self._owner_allowed_transitions.get(self.status, set())
        else:
            raise Exception("User role not permitted to update status.")

        if new_status in allowed:
            logger.info(f"Transition from '{self.status}' to '{new_status}' is allowed.")
            self.status = new_status
        else:
            raise Exception(f"Transition from '{self.status}' to '{new_status}' is not allowed.")
