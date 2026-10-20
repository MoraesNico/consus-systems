"""`manage.py checar_contraste`: recalcula a tabela §3 do design system a partir de tokens.css."""

import sys

from django.core.management.base import BaseCommand

from apps.core import design_tokens


class Command(BaseCommand):
    help = "Verifica o contraste WCAG 2.1 de todos os pares de cores permitidos pelo design system."

    def handle(self, *args, **options):
        pares = design_tokens.avaliar_pares(design_tokens.PARES_CONTRASTE)
        largura = max(len(f"{p['primeiro_plano']} / {p['fundo']}") for p in pares)
        for par in pares:
            nome = f"{par['primeiro_plano']} / {par['fundo']}".ljust(largura)
            minimo = "isento" if par["isento"] else f"{par['minimo']:.1f}:1"
            resultado = "ISENTO" if par["isento"] else ("AA" if par["aprovado"] else "FALHA")
            linha = f"{nome}  {par['razao']:>6.2f}:1  mín. {minimo:<7}  {resultado}"
            estilo = self.style.SUCCESS if par["aprovado"] else self.style.ERROR
            self.stdout.write(estilo(linha))
        reprovados = [p for p in pares if not p["aprovado"]]
        self.stdout.write(f"{len(pares)} pares verificados, {len(reprovados)} reprovado(s).")
        if reprovados:
            sys.exit(1)
