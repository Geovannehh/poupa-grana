"""Production entrypoint. Migrations belong to the pre-deploy phase."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def gunicorn_arguments(environment):
    try:
        port = int(environment.get("PORT", "8000"))
        workers = int(environment.get("WEB_CONCURRENCY", "2"))
        if not 1 <= port <= 65535 or not 1 <= workers <= 8:
            raise ValueError
    except ValueError:
        raise ValueError("PORT ou WEB_CONCURRENCY inválidos.") from None
    return [
        "gunicorn",
        "config.wsgi:application",
        "--bind",
        f"0.0.0.0:{port}",
        "--workers",
        str(workers),
        "--timeout",
        "60",
        "--error-logfile",
        "-",
    ]


def main():
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.railway")
    arguments = gunicorn_arguments(os.environ)
    import django
    from django.core.management import call_command

    django.setup()
    call_command("collectstatic", interactive=False, verbosity=0)
    # exec forwards shutdown signals directly to Gunicorn; no shell interpolation.
    os.execvp(arguments[0], arguments)


if __name__ == "__main__":
    main()
