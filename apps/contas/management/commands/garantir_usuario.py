"""Cria o usuário inicial se não existir; nunca troca a senha de um existente (006)."""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Garante um usuário administrador (CONSUS_USUARIO / CONSUS_SENHA)."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default=os.environ.get("CONSUS_USUARIO"))
        parser.add_argument("--senha", default=os.environ.get("CONSUS_SENHA"))

    def handle(self, *args, usuario=None, senha=None, **opcoes):
        if not usuario or not senha:
            raise CommandError("Informe --usuario e --senha (ou CONSUS_USUARIO e CONSUS_SENHA).")
        Usuario = get_user_model()
        if Usuario.objects.filter(username__iexact=usuario).exists():
            self.stdout.write(f"Usuário {usuario} já existe; senha mantida.")
            return
        Usuario.objects.create_superuser(username=usuario, password=senha, email="")
        self.stdout.write(self.style.SUCCESS(f"Usuário {usuario} criado."))
