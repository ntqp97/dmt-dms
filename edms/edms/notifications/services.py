import logging

from fcm_django.models import FCMDevice
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from edms.notifications.models import Notification, NotificationReceiver

logger = logging.getLogger(__name__)


class FirebaseService:
    @staticmethod
    def send_notification_to_multiple_devices(devices, title, body, image=None, data=None):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                ),
                data=data or {}
            )
            response = devices.send_message(message)
            return {"success": True, "response": response}
        except (FirebaseError, ValueError) as e:
            logger.error(str(e))
            raise Exception(e)


class NotificationService:
    @staticmethod
    def send_notification_to_users(sender, receivers, title, body, image=None, data=None):
        devices = FCMDevice.objects.filter(user__in=receivers)
        users_with_devices = set(devices.values_list("user", flat=True))
        users_without_devices = [user for user in receivers if user.id not in users_with_devices]
        if devices.exists():
            notification = Notification.objects.create(
                created_by=sender,
                title=title,
                body=body,
                data=data,
            )

            notification_receivers = []
            for user_id in users_with_devices:
                notification_receivers.append(
                    NotificationReceiver(
                        created_by=sender,
                        notification=notification,
                        receiver_id=user_id,
                        is_pushed=True
                    )
                )

            for user in users_without_devices:
                notification_receivers.append(
                    NotificationReceiver(
                        notification=notification,
                        receiver=user,
                        is_pushed=False
                    )
                )

            NotificationReceiver.objects.bulk_create(notification_receivers)
            FirebaseService.send_notification_to_multiple_devices(devices, title, body, image, data)
