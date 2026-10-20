"""`python manage.py movimentar <produto> entrada|saida <quantidade> [--obs "..."]` (FR-031).

Paridade de terminal com a proposta original de app de console: usa o mesmo serviço da web.
"""

import re
import unicodedata

from django.core.management.base import BaseCommand, CommandError

from apps.movimentacoes.forms import QuantidadeField
from apps.movimentacoes.models import OBSERVACAO_MAX, TipoMovimentacao
from apps.movimentacoes.services import MovimentacaoError, registrar_movimentacao

TIPOS = {"entrada": TipoMovimentacao.ENTRADA, "saida": TipoMovimentacao.SAIDA}


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))


class Command(BaseCommand):
    help = "Registra uma entrada ou saída/venda pelo terminal."

    def add_arguments(self, parser):
        parser.add_argument("produto", help="ID do produto: 12, #12 ou #0012")
        parser.add_argument("tipo", help="entrada ou saida")
        parser.add_argument("quantidade", help="inteiro de 1 a 1.000.000")
        parser.add_argument("--obs", default="", help="observação (nº da nota, cliente…)")

    def handle(self, *args, produto, tipo, quantidade, obs, **options):
        casou = re.fullmatch(r"#?\s*([0-9]+)", produto.strip())
        if not casou:
            raise CommandError("Informe o produto pelo ID (ex.: 12, #12 ou #0012).")
        tipo_normalizado = TIPOS.get(_sem_acentos(tipo.strip().lower()))
        if tipo_normalizado is None:
            raise CommandError("Tipo inválido: use entrada ou saida.")
        campo = QuantidadeField()
        try:
            valor = campo.clean(quantidade)
        except Exception as erro:
            raise CommandError(" ".join(getattr(erro, "messages", [str(erro)]))) from erro
        if len(obs.strip()) > OBSERVACAO_MAX:
            raise CommandError(f"Use no máximo {OBSERVACAO_MAX} caracteres na observação.")
        try:
            mov = registrar_movimentacao(
                produto_id=int(casou.group(1)),
                tipo=tipo_normalizado,
                quantidade=valor,
                observacao=obs,
            )
        except MovimentacaoError as erro:
            raise CommandError(str(erro)) from erro
        self.stdout.write(self.style.SUCCESS(mov.mensagem_confirmacao))
