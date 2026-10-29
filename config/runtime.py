"""Validate environment without connecting to a database or exposing its URL."""
import secrets
from urllib.parse import urlsplit

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def configuration(environment, *, testing=False, production=False):
    secret = environment.get("SECRET_KEY", "").strip()
    if testing and not secret:
        secret = secrets.token_urlsafe(64)
    if len(secret) < 50 or secret.startswith(("django-insecure-", "change-me", "example")):
        raise ImproperlyConfigured("SECRET_KEY deve ser própria e ter ao menos 50 caracteres.")

    hosts = [host.strip() for host in environment.get("ALLOWED_HOSTS", "").split(",")
             if host.strip()]
    if not hosts and not production:
        hosts = ["localhost", "127.0.0.1", "[::1]"]
    if not hosts or any("*" in host or "/" in host or "://" in host for host in hosts):
        raise ImproperlyConfigured("ALLOWED_HOSTS deve listar hosts explícitos, sem curingas.")

    url = environment.get("DATABASE_URL", "")
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
            raise ValueError
        if not parsed.path.strip("/") or not parsed.username:
            raise ValueError
        database = dj_database_url.parse(url, conn_max_age=0, conn_health_checks=True)
        # Bound connection establishment for readiness and management commands.
        database.setdefault("OPTIONS", {}).setdefault("connect_timeout", 3)
    except (ValueError, KeyError):
        raise ImproperlyConfigured("DATABASE_URL deve ser uma URL PostgreSQL válida.") from None

    if production and database.get("OPTIONS", {}).get("sslmode") not in {
        "require", "verify-ca", "verify-full"
    }:
        raise ImproperlyConfigured("PostgreSQL de produção requer sslmode seguro explícito.")

    return {"SECRET_KEY": secret, "ALLOWED_HOSTS": hosts, "DATABASES": {"default": database}}
