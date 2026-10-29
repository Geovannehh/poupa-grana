import base64
import secrets
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from integrations.models import ExportCredential
from ledger.models import Entry, Purchase
from workspaces.models import Membership, Workspace

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


@pytest.fixture
def export_access():
    User = get_user_model()
    owner = User.objects.create_user(username="export_owner", password=None)
    member = User.objects.create_user(username="export_member", password=None)
    company = Workspace.objects.create(name="Export", kind="business", owner=owner)
    link = Membership.objects.create(workspace=company, user=member)
    for user, description in [(owner, "owner_only"), (member, "member_only")]:
        purchase = Purchase.objects.create(workspace=company, creator=user)
        Entry.objects.create(
            workspace=company,
            creator=user,
            purchase=purchase,
            description=description,
            category="Outros",
            kind="expense",
            amount="10.00",
            occurred_on=timezone.localdate(),
            due_on=timezone.localdate(),
        )
    secret = secrets.token_urlsafe(20)
    key = ExportCredential.objects.create(
        user=member, workspace=company, secret_hash=make_password(secret)
    )
    header = "Basic " + base64.b64encode(f"{key.pk}:{secret}".encode()).decode()
    return member, company, link, key, header


def test_export_requires_dedicated_auth_even_with_session(client, export_access):
    client.force_login(export_access[0])
    assert client.get("/api/bi/v1/entries/").status_code == 401


def test_export_filters_rows_by_user_and_ignores_injected_scope(client, export_access):
    response = client.get(
        "/api/bi/v1/entries/?workspace=999&user=999", HTTP_AUTHORIZATION=export_access[-1]
    )
    assert response.status_code == 200
    assert [row["description"] for row in response.json()["results"]] == ["member_only"]
    assert response["Cache-Control"] == "no-store"


@pytest.mark.parametrize("mode", ["revoke", "expire", "remove_membership", "inactive_user"])
def test_revoked_or_expired_or_removed_access_is_denied(client, export_access, mode):
    member, _, link, key, header = export_access
    if mode == "revoke":
        key.active = False
        key.save()
    elif mode == "expire":
        key.expires_at = timezone.now() - timedelta(seconds=1)
        key.save()
    elif mode == "remove_membership":
        link.active = False
        link.save()
    else:
        member.is_active = False
        member.save()
    assert client.get("/api/bi/v1/entries/", HTTP_AUTHORIZATION=header).status_code == 401


def test_export_is_get_only_and_rejects_bad_page(client, export_access):
    header = export_access[-1]
    assert client.post("/api/bi/v1/entries/", HTTP_AUTHORIZATION=header).status_code == 405
    assert client.get("/api/bi/v1/entries/?page=0", HTTP_AUTHORIZATION=header).status_code == 400
    assert client.get("/api/bi/v1/entries/", HTTP_AUTHORIZATION="Basic INVALID").status_code == 401


def test_credential_secret_is_only_shown_once(client, export_access):
    member = export_access[0]
    client.force_login(member)
    response = client.post("/integracoes/")
    assert response.status_code == 200
    assert response.context["new_secret"]
    assert response["Cache-Control"] == "no-store"
    secret = response.context["new_secret"]
    assert secret.encode() not in client.get("/integracoes/").content
    assert not ExportCredential.objects.filter(secret_hash=secret).exists()
