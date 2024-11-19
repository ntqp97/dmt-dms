from django.db import models


class SoftDeleteManager(models.Manager):
    """Soft Delete manager"""
    def get_queryset(self):
        """
        Getting queryset function for Soft Delete models.
        """
        return super().get_queryset().filter(deleted=False)


class SoftDeleteModel(models.Model):
    """
    Abstract model to model tables having soft-deletable objects
    """
    deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.manager.Manager()

    def delete(self, *args, **kwargs):
        """
        Delete function for soft deleting a model object instance.
        """
        self.deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        """
        Undelete function for recovering a model object instance.
        """
        self.deleted = False
        self.save()

    def permanent_delete(self, *args, **kwargs):
        """
        Delete function for permanently deleting a model object instance.
        """
        super().delete(*args, **kwargs)

    class Meta:
        """Metaclass for Soft Delete Model"""
        abstract = True
