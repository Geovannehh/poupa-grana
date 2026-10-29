import json
import os
import secrets
import subprocess
import sys

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from scripts.start_production import gunicorn_arguments
from workspaces.models import Workspace


def production_environment():
    return dict(
        os.environ,
        DJANGO_SETTINGS_MODULE="config.settings.railway",
        SECRET_KEY=secrets.token_urlsafe(64),
        DATABASE_URL="postgresql://fictitious:fictitious@localhost/unused?sslmode=require",
        ALLOWED_HOSTS="finance.example.invalid",
        RAILWAY_PROJECT_ID="test-context-only",
    )


def test_railway_proxy_configuration_is_explicit_and_narrow():
    command = (
        "import django,json;django.setup();from django.conf import settings as s;"
        "print(json.dumps({'hosts':s.ALLOWED_HOSTS,'proxy':s.SECURE_PROXY_SSL_HEADER,"
        "'exempt':s.SECURE_REDIRECT_EXEMPT,'debug':s.DEBUG,'middleware':s.MIDDLEWARE}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        env=production_environment(),
        capture_output=True,
        text=True,
        check=True,
    )
    settings = json.loads(result.stdout)
    assert settings["hosts"] == ["finance.example.invalid", "healthcheck.railway.app"]
    assert settings["proxy"] == ["HTTP_X_FORWARDED_PROTO", "https"]
    assert settings["exempt"] == ["^health/$"]
    assert settings["debug"] is False
    assert settings["middleware"][1] == "whitenoise.middleware.WhiteNoiseMiddleware"


def test_railway_settings_refuse_to_trust_proxy_without_platform_context():
    environment = production_environment()
    environment.pop("RAILWAY_PROJECT_ID")
    result = subprocess.run(
        [sys.executable, "-c", "import django;django.setup()"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "contexto da plataforma" in result.stderr


@pytest.mark.parametrize(
    "port,workers", [("invalid", "2"), ("0", "2"), ("70000", "2"), ("8080", "99")]
)
def test_invalid_production_process_configuration_fails_closed(port, workers):
    with pytest.raises(ValueError):
        gunicorn_arguments({"PORT": port, "WEB_CONCURRENCY": workers})


def test_production_command_uses_port_without_shell_interpolation():
    command = gunicorn_arguments({"PORT": "8181", "WEB_CONCURRENCY": "2"})
    assert command[:2] == ["gunicorn", "config.wsgi:application"]
    assert "0.0.0.0:8181" in command
    assert "--reload" not in command


@pytest.mark.postgres
@pytest.mark.django_db
def test_bootstrap_requires_private_variables_and_never_creates_default_owner(monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_OWNER_USERNAME", raising=False)
    monkeypatch.delenv("BOOTSTRAP_OWNER_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("initialize_owner")
    assert not get_user_model().objects.exists()


@pytest.mark.postgres
@pytest.mark.django_db
def test_bootstrap_is_idempotent_and_does_not_reset_existing_password(monkeypatch, capsys):
    password = secrets.token_urlsafe(24)
    monkeypatch.setenv("BOOTSTRAP_OWNER_USERNAME", "first_owner")
    monkeypatch.setenv("BOOTSTRAP_OWNER_PASSWORD", password)
    call_command("initialize_owner")
    user = get_user_model().objects.get()
    assert user.check_password(password)
    assert not user.is_superuser and not user.is_staff
    assert set(Workspace.objects.values_list("kind", flat=True)) == {"personal", "business"}
    monkeypatch.setenv("BOOTSTRAP_OWNER_PASSWORD", secrets.token_urlsafe(24))
    call_command("initialize_owner")
    user.refresh_from_db()
    assert user.check_password(password)
    assert get_user_model().objects.count() == 1
    assert Workspace.objects.count() == 2
    assert password not in capsys.readouterr().out


@pytest.mark.postgres
@pytest.mark.django_db
def test_only_health_endpoint_is_exempt_from_https_redirect(client):
    with override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r"^health/$"],
        ALLOWED_HOSTS=["healthcheck.railway.app", "finance.example.invalid"],
    ):
        health = client.get("/health/", HTTP_HOST="healthcheck.railway.app")
        assert health.status_code == 200
        assert client.get("/entrar/", HTTP_HOST="finance.example.invalid").status_code == 301


@pytest.mark.postgres
@pytest.mark.django_db
def test_static_assets_are_collected_and_served_without_debug(client, tmp_path):
    from django.conf import settings

    storage = {
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
    }
    middleware = [
        settings.MIDDLEWARE[0],
        "whitenoise.middleware.WhiteNoiseMiddleware",
        *settings.MIDDLEWARE[1:],
    ]
    with override_settings(
        STATIC_ROOT=tmp_path,
        STATIC_URL="/static/",
        STORAGES=storage,
        MIDDLEWARE=middleware,
        DEBUG=False,
    ):
        call_command("collectstatic", interactive=False, verbosity=0)
        response = client.get("/static/workspaces/app.css")
        assert response.status_code == 200
        content = b"".join(response.streaming_content)
        assert b".sidebar" in content
        response.close()
