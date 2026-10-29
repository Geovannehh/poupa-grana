"""One-time owner provisioning from private deployment variables; never resets access."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from workspaces.models import Workspace


class Command(BaseCommand):
    help = "Inicializa o proprietário via variáveis privadas, sem imprimir ou redefinir senhas."

    def handle(self, *args, **options):
        with transaction.atomic():
            # Serialize concurrent pre-deploy jobs for this application database.
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(71648291)")
            User = get_user_model()
            if User.objects.exists():
                self.stdout.write("Instalação já inicializada; usuários preservados.")
                return
            username = os.environ.get("BOOTSTRAP_OWNER_USERNAME", "").strip()
            password = os.environ.get("BOOTSTRAP_OWNER_PASSWORD", "")
            if not username or not password:
                raise CommandError("Defina as variáveis privadas de inicialização do proprietário.")
            user = User(username=username)
            try:
                user.full_clean(exclude=["password"])
                validate_password(password, user)
            except ValidationError:
                raise CommandError(
                    "Usuário ou senha inicial não atendem às regras de segurança."
                ) from None
            user.set_password(password)
            user.save()
            Workspace.objects.create(name="Meu pessoal", kind="personal", owner=user)
            Workspace.objects.create(name="Minha empresa", kind="business", owner=user)
        self.stdout.write("Proprietário criado. Remova as variáveis de bootstrap da hospedagem.")
