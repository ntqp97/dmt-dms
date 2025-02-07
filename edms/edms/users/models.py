import logging
from typing import ClassVar

import jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import datetime

from ..common.basemodels import BaseModel
from ..common.storage_backends import PublicMediaStorage
from ..organization.models import OrganizationUnit
from .managers import UserManager
logger = logging.getLogger(__name__)


def get_path_user_avatar(instance, filename):
    return f"user/avatar/{filename}"


class User(AbstractUser):
    """
    Default custom user model for EDMS.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = models.EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    phone_number = models.CharField(max_length=15, null=True, blank=True, unique=True)
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    department = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    gender = models.BooleanField(default=True)
    email_checked = models.BooleanField(default=False)
    external_user_id = models.CharField(max_length=255, null=True, blank=True)
    citizen_identification = models.CharField(max_length=50, null=True, blank=True, unique=True)
    signature_images = models.ManyToManyField(
        "assets.Asset",
        through="UserSignature",
        through_fields=("user", "signature_image"),
        related_name="user_signatures"
    )
    avatar = models.FileField(
        upload_to=get_path_user_avatar,
        storage=PublicMediaStorage(),
        blank=True,
        null=True,
        default=None
    )
    birthdate = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    def create_signature_image(self, file, file_type, is_default):
        import mimetypes
        from edms.assets.models import Asset

        if is_default:
            UserSignature.objects.filter(user=self, is_default=True).update(is_default=False)
        else:
            if not UserSignature.objects.filter(user=self).exists():
                is_default = True

        asset = Asset.objects.create(
            file_type=file_type,
            file=file,
            size=file.size,
            asset_name=file.name,
            mime_type=(
                mimetypes.guess_type(file.name)[0]
                if mimetypes.guess_type(file.name)[0]
                else file.content_type
            ),
            created_by=self,
        )

        UserSignature.objects.create(
            user=self,
            signature_image=asset,
            is_default=is_default,
        )

    @staticmethod
    def verify_reset_token(token):
        try:
            data = jwt.decode(
                token,
                settings.SECRET_KEY,
                leeway=datetime.timedelta(seconds=10),
                algorithms=["HS256"]
            )
        except Exception as e:
            logger.error("Error: %s", e)
            return None
        return User.objects.get(citizen_identification=data.get("citizen_identification"))

    def get_reset_token(self):
        expire_time = datetime.timedelta(seconds=settings.EXPIRED_TIME_VERIFY_EMAIL)
        reset_token = jwt.encode(
            {
                "citizen_identification": self.citizen_identification,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc) + expire_time
            },
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        return reset_token


class UserSignature(BaseModel):
    user = models.ForeignKey(
        "users.User",
        related_name="user_signature_entries",
        on_delete=models.CASCADE,
    )
    signature_image = models.ForeignKey(
        "assets.Asset",
        related_name="signature_entries_for_users",
        on_delete=models.CASCADE,
    )
    is_default = models.BooleanField(default=False)


class ForgotPasswordRequest(models.Model):
    email = models.EmailField(blank=True, null=True)
    ip_address = models.CharField(max_length=40, default=None, null=True, blank=True)
    request_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [

            models.Index(
                fields=[
                    "ip_address",
                ]
            ),
        ]

    def __str__(self) -> str:
        return f"{self.email} - {self.ip_address}"
