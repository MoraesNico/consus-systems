"""`python manage.py resumo_financeiro` — indicadores do Passo 3 no terminal (009)."""

import json
import sys

from django.core.management.base import BaseCommand
from django.db import DatabaseError

from apps.core.dinheiro import formatar_moeda
from apps.core.periodos import ROTULOS, PeriodoInvalidoError, resolver_periodo
from apps.financeiro.selectors import resumo_financeiro


class Command(BaseCommand):
    help = "Mostra valor do estoque, faturamento, lucro bruto e saldo do caixa."

    def add_arguments(self, parser):
        parser.add_argument("--periodo", default="tudo", choices=list(ROTULOS))
        parser.add_argument("--de")
        parser.add_argument("--ate")
        parser.add_argument("--formato", default="texto", choices=["texto", "json"])
        parser.add_argument("--falhar-se-negativo", action="store_true")

    def handle(self, *args, **opcoes):
        try:
            periodo = resolver_periodo(opcoes["periodo"], opcoes["de"], opcoes["ate"])
            r = resumo_financeiro(periodo)
        except (PeriodoInvalidoError, DatabaseError) as erro:
            self.stderr.write(f"Erro: {erro}")
            sys.exit(2)
        if opcoes["formato"] == "json":
            dados = {
                "periodo": periodo.chave,
                "de": periodo.de and periodo.de.isoformat(),
                "ate": periodo.ate and periodo.ate.isoformat(),
                "valor_estoque": str(r.valor_estoque),
                "receitas": str(r.receitas),
                "despesas": str(r.despesas),
                "custo_vendido": str(r.custo_vendido),
                "lucro_bruto": str(r.lucro_bruto),
                "saldo_caixa": str(r.saldo_caixa),
                "caixa_negativo": r.caixa_negativo,
            }
            self.stdout.write(json.dumps(dados, ensure_ascii=False, indent=2))
        else:
            linhas = [
                f"CONSUS — RESUMO FINANCEIRO ({periodo.rotulo})",
                f"Valor total do estoque: {formatar_moeda(r.valor_estoque)}",
                f"Faturamento: {formatar_moeda(r.receitas)}",
                f"Lucro bruto realizado: {formatar_moeda(r.lucro_bruto)}",
                f"Despesas: {formatar_moeda(r.despesas)}",
                f"Saldo do caixa: {formatar_moeda(r.saldo_caixa)}",
            ]
            if r.caixa_negativo:
                linhas.append("⚠ CAIXA NEGATIVO: as despesas superam as receitas no período.")
            self.stdout.write("\n".join(linhas))
        if opcoes["falhar_se_negativo"] and r.caixa_negativo:
            sys.exit(1)
