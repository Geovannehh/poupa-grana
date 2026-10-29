import importlib
import os
import secrets
import subprocess
import sys
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.runtime import configuration


def valid_environment():
    return {
        "SECRET_KEY": secrets.token_urlsafe(64),
        "DATABASE_URL": "postgresql://test_role:fictitious@127.0.0.1/poupa_grana_ci",
        "ALLOWED_HOSTS": "finance.example.invalid",
    }


@pytest.mark.parametrize("key", ["SECRET_KEY", "DATABASE_URL", "ALLOWED_HOSTS"])
def test_production_requires_explicit_configuration(key):
    env = valid_environment()
    env["DATABASE_URL"] += "?sslmode=require"
    env.pop(key)
    with pytest.raises(ImproperlyConfigured):
        configuration(env, production=True)


@pytest.mark.parametrize("url", ["sqlite:///data.db", "", "postgresql:///missing-host",
                                "postgresql://user:private@host:wrong/db"])
def test_invalid_database_does_not_expose_credentials(url):
    env = valid_environment()
    env["DATABASE_URL"] = url
    with pytest.raises(ImproperlyConfigured) as error:
        configuration(env)
    assert "private" not in str(error.value)
    assert "sqlite" not in str(error.value)


def test_production_requires_encrypted_database_connection():
    with pytest.raises(ImproperlyConfigured, match="sslmode"):
        configuration(valid_environment(), production=True)


@pytest.mark.parametrize("hosts", ["*", "*.example.invalid", "https://host.invalid/path"])
def test_wildcard_and_url_hosts_are_rejected(hosts):
    env = valid_environment()
    env["ALLOWED_HOSTS"] = hosts
    with pytest.raises(ImproperlyConfigured):
        configuration(env)


def test_production_ignores_debug_environment_and_sets_secure_cookies():
    env = valid_environment()
    env["DATABASE_URL"] += "?sslmode=verify-full"
    env["DEBUG"] = "1"
    with patch.dict(os.environ, env, clear=True):
        module = importlib.import_module("config.settings.production")
        module = importlib.reload(module)
    assert module.DEBUG is False
    assert module.SESSION_COOKIE_SECURE and module.CSRF_COOKIE_SECURE
    assert module.SECURE_SSL_REDIRECT
    assert module.DATABASES["default"]["OPTIONS"]["sslmode"] == "verify-full"


def test_wsgi_and_asgi_can_be_imported_with_valid_production_environment():
    env = dict(os.environ, **valid_environment())
    env["DATABASE_URL"] += "?sslmode=require"
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
    result = subprocess.run(
        [sys.executable, "-c", "import config.wsgi; import config.asgi"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, "Application imports must succeed without connecting to DB"


def test_test_settings_cannot_fall_back_to_application_database():
    env = dict(os.environ)
    env.pop("TEST_DATABASE_URL", None)
    env["DATABASE_URL"] = valid_environment()["DATABASE_URL"]
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
    result = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
