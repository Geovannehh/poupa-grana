from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Workspace(models.Model):
    class Kind(models.TextChoices):
        PERSONAL = "personal", "Pessoal"
        BUSINESS = "business", "Empresa"

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "kind"], name="owner_kind_unique")]

    def __str__(self):
        return self.name


class Membership(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace", "user"], name="workspace_user_unique")
        ]

    def clean(self):
        if self.workspace.kind != Workspace.Kind.BUSINESS:
            raise ValidationError("O espaço pessoal não aceita membros.")
