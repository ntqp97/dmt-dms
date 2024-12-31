from django.db import models

from edms.common.basemodels import BaseModel


# Create your models here.
class OrganizationUnit(BaseModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    unit_type = models.CharField(max_length=50)
    level = models.IntegerField()

    def __str__(self):
        return self.name

    def get_children(self):
        return OrganizationUnit.objects.filter(parent=self)

    def get_ancestor(self, levels_up=1):
        """Returns ancestor."""
        ancestor = self
        for _ in range(levels_up):
            if ancestor.parent:
                ancestor = ancestor.parent
            else:
                return None
        return ancestor

    def get_all_ancestors(self):
        """Returns list all ancestors."""
        ancestors = []
        ancestor = self.parent
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor.parent
        return ancestors

    def as_tree(self):
        """Returns the unit and its children as a tree."""
        return {
            "id": self.id,
            "name": self.name,
            "unit_type": self.unit_type,
            "level": self.level,
            "children": [child.as_tree() for child in self.get_children()],
        }
