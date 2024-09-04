from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import SET_NULL
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..organization.models import OrganizationUnit
from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for EDMS.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    phone_number = CharField(max_length=15, null=True, blank=True, unique=True)
    organization_unit = ForeignKey(
        OrganizationUnit,
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name="users",
    )
    department = CharField(max_length=255, null=True, blank=True)
    position = CharField(max_length=255, null=True, blank=True)
    gender = BooleanField(default=True)
    email_checked = BooleanField(default=False)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})
