import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from workspaces.models import Workspace


def expires_default():
    return timezone.now() + timedelta(days=90)


class ExportCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    secret_hash = models.CharField(max_length=200)
    expires_at = models.DateTimeField(default=expires_default)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
