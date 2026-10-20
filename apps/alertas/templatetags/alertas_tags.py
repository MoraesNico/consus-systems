"""Tags da feature 004: contador do menu e lista de cobertura do painel."""

from django import template
from django.conf import settings
from django.urls import NoReverseMatch, reverse

from ..selectors import total_em_alerta

register = template.Library()


@register.inclusion_tag("alertas/partials/contador.html")
def contador_alertas():
    """Renderiza o contador no menu; nada se a rota alertas:contador não existir."""
    try:
        reverse("alertas:contador")
    except NoReverseMatch:
        return {"ausente": True}
    return {"total": total_em_alerta(), "intervalo": settings.ALERTAS_INTERVALO_SEGUNDOS}


@register.inclusion_tag("alertas/partials/lista_cobertura.html")
def lista_cobertura(produtos):
    return {"produtos": produtos}


@register.filter
def limitar_movimentacao(valor):
    """Quantidade para o atalho de entrada: até 1.000.000 por movimentação (003)."""
    from apps.movimentacoes.models import QUANTIDADE_MAXIMA_MOVIMENTACAO

    if not valor:
        return None
    return min(int(valor), QUANTIDADE_MAXIMA_MOVIMENTACAO)
