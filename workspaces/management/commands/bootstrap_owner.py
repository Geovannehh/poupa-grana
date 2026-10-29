from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from workspaces.models import Workspace


class Command(BaseCommand):
    help = "Cria o proprietário e seus espaços, somente pelo console local."

    def handle(self, *args, **options):
        if Workspace.objects.exists() or get_user_model().objects.exists():
            raise CommandError("Bootstrap já realizado; não altera usuários existentes.")
        username = input("Usuário do proprietário: ").strip()
        user = get_user_model()(username=username)
        user.full_clean(exclude=["password"])
        password = getpass("Senha: ")
        validate_password(password, user)
        if password != getpass("Confirme a senha: "):
            raise CommandError("As senhas não coincidem.")
        user.set_password(password)
        with transaction.atomic():
            user.save()
            Workspace.objects.create(name="Meu pessoal", kind="personal", owner=user)
            Workspace.objects.create(name="Minha empresa", kind="business", owner=user)
        self.stdout.write("Proprietário e espaços criados; nenhuma senha foi exibida.")
