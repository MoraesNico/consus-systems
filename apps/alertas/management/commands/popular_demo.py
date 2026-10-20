"""`python manage.py popular_demo` — dados de demonstração idempotentes (FR-034, FR-035)."""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from apps.alertas.demo import popular
from apps.movimentacoes.services import MovimentacaoError


class Command(BaseCommand):
    help = "Cria produtos e movimentações de demonstração (não altera os que já existem)."

    def handle(self, *args, **options):
        try:
            criados, existentes, movimentacoes = popular()
        except (DatabaseError, MovimentacaoError) as erro:
            raise CommandError(f"Não foi possível popular os dados: {erro}", returncode=2) from erro
        self.stdout.write(
            f"Dados de demonstração: {criados} produto(s) criado(s), {existentes} já existia(m)."
        )
        self.stdout.write(f"Movimentações registradas: {movimentacoes}.")
