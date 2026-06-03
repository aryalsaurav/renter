from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-]{7,20}$",
    message="Enter a valid phone number (7-20 digits, optional + and separators).",
)


class User(AbstractUser):
    """Email-as-username custom user.

    The ``username`` field from AbstractUser is removed; ``email`` is the login.
    Contact fields (email, phone) are intentionally treated as private and are
    never exposed by the public listing serializers/templates.
    """

    username = None
    email = models.EmailField(_("email address"), unique=True)
    phone = models.CharField(
        max_length=20, blank=True, validators=[phone_validator]
    )
    # Owners must be verified before their listings can be auto-published.
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified owners can publish listings without manual review.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        full = self.get_full_name()
        return full or self.email.split("@")[0]


class Profile(models.Model):
    """Extra public-facing profile info for a user."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    city = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.email}>"
