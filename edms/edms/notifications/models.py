from django.db import models

from edms.common.basemodels import BaseModel
from django.utils.timezone import now


# Create your models here.
class Notification(BaseModel):
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    receivers = models.ManyToManyField(
        "users.User",
        through="NotificationReceiver",
        through_fields=("notification", "receiver"),
    )


class NotificationReceiver(BaseModel):
    notification = models.ForeignKey(
        "notifications.Notification",
        related_name="notification_receivers",
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        "users.User",
        related_name="received_notifications",
        on_delete=models.CASCADE,
    )
    is_push = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def mark_as_read(self):
        self.is_read = True
        self.read_at = now()
        self.updated_by = self.receiver
        self.save()

    def is_unread(self):
        return not self.is_read
