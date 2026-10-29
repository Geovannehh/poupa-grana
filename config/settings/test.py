import os

from config.runtime import configuration

from .base import *  # noqa: F403

# A distinct, disposable database URL prevents accidental use of a production URL.
validated = configuration({
    "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", ""),
    "ALLOWED_HOSTS": "testserver,localhost,127.0.0.1",
}, testing=True)
SECRET_KEY = validated["SECRET_KEY"]
ALLOWED_HOSTS = validated["ALLOWED_HOSTS"]
DATABASES = validated["DATABASES"]
DATABASES["default"]["TEST"] = {"NAME": "test_poupa_grana"}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DEBUG = False
