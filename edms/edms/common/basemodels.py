from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="created_%(class)ss",
        default=None,
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="updated_%(class)ss",
        default=None,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True

    def init_data(self, request):
        self.created_by = request.user
        self.save()
