from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..common.basemodels import BaseModel
from ..organization.models import OrganizationUnit
from .managers import UserManager


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
