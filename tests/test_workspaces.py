import secrets

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from workspaces.access import accessible_spaces
from workspaces.models import Membership, Workspace

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


@pytest.fixture
def team():
    User = get_user_model()
    owner = User.objects.create_user(username="owner", password=None)
    member = User.objects.create_user(username="member_one", password=None)
    other = User.objects.create_user(username="member_two", password=None)
    private = Workspace.objects.create(name="Pessoal", kind="personal", owner=owner)
    company = Workspace.objects.create(name="Empresa", kind="business", owner=owner)
    link = Membership.objects.create(workspace=company, user=member)
    other_link = Membership.objects.create(workspace=company, user=other)
    return owner, member, private, company, link, other_link


def test_anonymous_is_redirected_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.url.startswith("/entrar/")


def test_owner_and_members_have_separate_space_queries(team):
    owner, member, private, company, *_ = team
    assert set(accessible_spaces(owner)) == {private, company}
    assert list(accessible_spaces(member)) == [company]


def test_member_cannot_select_personal_space(client, team):
    _, member, private, *_ = team
    client.force_login(member)
    assert client.post("/espaco/", {"workspace": private.pk}).status_code == 404


def test_revoked_membership_invalidates_saved_session(client, team):
    _, member, _, company, link, _ = team
    client.force_login(member)
    session = client.session
    session["workspace_id"] = company.pk
    session.save()
    link.active = False
    link.save()
    assert client.get("/").status_code == 404


def test_member_cannot_administer_team_even_if_staff(client, team):
    _, member, *_ = team
    member.is_staff = True
    member.save()
    client.force_login(member)
    assert client.get("/equipe/").status_code == 403
    assert client.post("/equipe/", {"username": "intruder"}).status_code == 403


def test_owner_can_create_non_admin_member(client, team):
    owner, _, _, company, *_ = team
    client.force_login(owner)
    client.post("/espaco/", {"workspace": company.pk})
    password = secrets.token_urlsafe(24)
    response = client.post("/equipe/", {"username": "new_member", "password": password})
    assert response.status_code == 302
    user = get_user_model().objects.get(username="new_member")
    assert user.check_password(password)
    assert not user.is_staff and not user.is_superuser
    assert list(accessible_spaces(user)) == [company]


def test_member_cannot_revoke_colleague(client, team):
    _, member, _, _, _, other = team
    client.force_login(member)
    assert client.post(f"/equipe/{other.pk}/revogar/").status_code == 403
    other.refresh_from_db()
    assert other.active


def test_unsafe_switch_requires_csrf(team):
    owner, _, _, company, *_ = team
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    assert client.post("/espaco/", {"workspace": company.pk}).status_code == 403


def test_logout_requires_post(client, team):
    client.force_login(team[0])
    assert client.get("/sair/").status_code == 405
    assert client.post("/sair/").status_code == 302
    assert client.get("/").status_code == 302


def test_malformed_space_id_is_404(client, team):
    client.force_login(team[0])
    assert client.post("/espaco/", {"workspace": "garbage"}).status_code == 404


def test_login_rejects_external_next_redirect(client):
    user = get_user_model().objects.create_user(username="login_test", password=None)
    password = secrets.token_urlsafe(24)
    user.set_password(password)
    user.save()
    response = client.post(
        "/entrar/?next=https://attacker.invalid",
        {
            "username": user.username,
            "password": password,
        },
    )
    assert response.status_code == 302
    assert response.url == "/"


def test_repeated_failed_login_is_rate_limited(client):
    for _ in range(10):
        response = client.post("/entrar/", {"username": "unknown", "password": "wrong"})
        assert response.status_code == 200
    response = client.post("/entrar/", {"username": "unknown", "password": "wrong"})
    assert response.status_code == 429
    assert response["Retry-After"] == "900"


def test_login_rate_keys_do_not_store_raw_username_or_ip(client):
    from accounts.models import LoginAttempt

    client.post("/entrar/", {"username": "sensitive_name", "password": "wrong"})
    attempt = LoginAttempt.objects.get()
    assert "sensitive_name" not in attempt.key
    assert "127.0.0.1" not in attempt.key
    assert len(attempt.key) == 64
