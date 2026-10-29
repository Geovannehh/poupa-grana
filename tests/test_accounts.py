import pytest
from django.contrib.auth import get_user_model
from django.db import connection


@pytest.mark.postgres
@pytest.mark.django_db
def test_initial_migration_creates_custom_user_without_default_admin():
    User = get_user_model()
    assert connection.vendor == "postgresql"
    assert User._meta.label == "accounts.User"
    assert not User.objects.exists()
    user = User.objects.create_user(username="person_one", password=None)
    user.refresh_from_db()
    assert not user.has_usable_password()
    assert not user.is_staff and not user.is_superuser
    assert user.pk is not None
