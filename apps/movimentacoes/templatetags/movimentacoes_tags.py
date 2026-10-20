"""Integração com as páginas de produto (contracts/integracao-produtos.md)."""

from django import template

from ..selectors import historico_do_produto

register = template.Library()


@register.inclusion_tag("movimentacoes/partials/acoes_rapidas.html")
def acoes_rapidas(produto, origem: str = "lista"):
    return {"produto": produto, "origem": origem}


@register.inclusion_tag("movimentacoes/partials/historico_produto.html")
def historico_produto(produto, oob: bool = False):
    return {"produto": produto, "movimentacoes": historico_do_produto(produto.pk), "oob": oob}
