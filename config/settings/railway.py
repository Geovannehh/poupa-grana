"""Only for Railway's documented TLS-terminating public proxy."""

import os

from django.core.exceptions import ImproperlyConfigured

from .production import *  # noqa: F403

if not os.environ.get("RAILWAY_PROJECT_ID"):
    raise ImproperlyConfigured("O perfil Railway exige contexto da plataforma.")

# Railway's public proxy sets X-Forwarded-Proto=https. Do not enable in local settings.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ALLOWED_HOSTS = [*ALLOWED_HOSTS, "healthcheck.railway.app"]  # noqa: F405
CSRF_TRUSTED_ORIGINS = [
    "https://" + host for host in ALLOWED_HOSTS if host != "healthcheck.railway.app"
]
# Readiness is the only HTTP endpoint exempt from the HTTPS redirect.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
MIDDLEWARE = [MIDDLEWARE[0], "whitenoise.middleware.WhiteNoiseMiddleware", *MIDDLEWARE[1:]]  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
