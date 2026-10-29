import os

from dotenv import load_dotenv

from config.runtime import configuration

from .base import *  # noqa: F403

load_dotenv(BASE_DIR / ".env", override=False)  # noqa: F405
validated = configuration(os.environ)
SECRET_KEY = validated["SECRET_KEY"]
ALLOWED_HOSTS = validated["ALLOWED_HOSTS"]
DATABASES = validated["DATABASES"]
# Explicit opt-in for local debugging only.
DEBUG = os.environ.get("DEBUG", "0") == "1"
