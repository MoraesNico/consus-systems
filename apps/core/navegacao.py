"""Itens da navegação principal (data-model §4).

Uma seção vira link sozinha quando a feature registra a rota com o nome do contrato;
até lá aparece como "(em breve)".
"""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse


@dataclass(frozen=True)
class ItemNavegacao:
    rotulo: str
    rota: str
    icone: str
    secao: str  # nome exato da rota (Painel) ou namespace (demais)


ITENS_NAVEGACAO = (
    ItemNavegacao("Painel", "core:painel", "layout-dashboard", "core:painel"),
    ItemNavegacao("Produtos", "produtos:lista", "package", "produtos"),
    ItemNavegacao("Movimentações", "movimentacoes:lista", "arrow-left-right", "movimentacoes"),
    ItemNavegacao("Financeiro", "financeiro:painel", "wallet", "financeiro"),
    ItemNavegacao("Alertas", "alertas:relatorio", "bell", "alertas"),
)


def url_se_existir(nome: str, *args, **kwargs) -> str | None:
    try:
        return reverse(nome, args=args or None, kwargs=kwargs or None)
    except NoReverseMatch:
        return None


def _ativo(item: ItemNavegacao, request) -> bool:
    match = getattr(request, "resolver_match", None)
    if match is None:
        return False
    if ":" in item.secao:
        return match.view_name == item.secao
    return item.secao in match.namespaces


def resolver_itens(request) -> list[dict]:
    itens = []
    for item in ITENS_NAVEGACAO:
        url = url_se_existir(item.rota)
        itens.append(
            {
                "rotulo": item.rotulo,
                "icone": item.icone,
                "url": url,
                "disponivel": url is not None,
                "ativo": url is not None and _ativo(item, request),
                "alertas": item.secao == "alertas",
            }
        )
    return itens
