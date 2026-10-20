"""Template tags do design system (`{% icone %}`), disponíveis em todos os templates."""

from django import template

register = template.Library()


@register.inclusion_tag("components/icone.html")
def icone(nome: str, tamanho: str = "sm", rotulo: str = ""):
    return {"nome": nome, "tamanho": tamanho, "rotulo": rotulo}


@register.filter
def porcentagem(valor, total) -> int:
    """Percentual inteiro (0–100) de `valor` em `total`; 0 quando total é 0."""
    try:
        valor, total = int(valor), int(total)
    except (TypeError, ValueError):
        return 0
    if total <= 0:
        return 0
    return max(0, min(100, valor * 100 // total))
