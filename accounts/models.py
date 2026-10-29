from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user established before the first migration; no finance fields yet."""


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
