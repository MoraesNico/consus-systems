"""`python manage.py varrer_estoque` — varredura de reposição no terminal (FR-027–FR-031).

Paridade com a proposta original (app de console): imprime "⚠ REPOSIÇÃO NECESSÁRIA" para cada
produto com quantidade atual igual ou abaixo do estoque mínimo de segurança.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from apps.alertas.exportacao import para_csv, para_json, para_texto
from apps.alertas.selectors import varrer


class Command(BaseCommand):
    help = "Varre o estoque e lista os produtos que precisam de reposição."

    def add_arguments(self, parser):
        parser.add_argument("--formato", choices=["texto", "csv", "json"], default="texto")
        parser.add_argument("--todos", action="store_true", help="inclui os produtos OK no fim")
        parser.add_argument(
            "--falhar-se-alerta",
            action="store_true",
            help="termina com código 1 se houver produto em alerta (útil em cron/CI)",
        )

    def _simbolo(self) -> str:
        codificacao = getattr(self.stdout._out, "encoding", None) or "utf-8"
        try:
            "⚠".encode(codificacao)
        except (UnicodeEncodeError, LookupError):
            return "(!)"
        return "⚠"

    def handle(self, *args, formato, todos, falhar_se_alerta, **options):
        try:
            resultado = varrer(incluir_ok=todos)
        except DatabaseError as erro:
            raise CommandError(
                f"Não foi possível consultar o estoque: {erro}", returncode=2
            ) from erro
        if formato == "csv":
            self.stdout.write(para_csv(resultado, bom=False), ending="")
        elif formato == "json":
            self.stdout.write(para_json(resultado))
        else:
            for linha, alerta in para_texto(resultado, simbolo=self._simbolo()):
                self.stdout.write(self.style.WARNING(linha) if alerta else linha)
        if falhar_se_alerta and resultado.total_em_alerta:
            raise CommandError(
                f"Há {resultado.total_em_alerta} produto(s) em alerta de reposição.", returncode=1
            )
