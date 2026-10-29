import os

from config.runtime import configuration

from .base import *  # noqa: F403

validated = configuration(os.environ, production=True)
SECRET_KEY = validated["SECRET_KEY"]
ALLOWED_HOSTS = validated["ALLOWED_HOSTS"]
DATABASES = validated["DATABASES"]
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
# Proxy trust must be reviewed in the Railway-specific task; never trust headers by default.
