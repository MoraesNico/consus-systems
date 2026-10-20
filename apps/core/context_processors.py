"""Contexto global da casca do Consus (contracts/layout-e-htmx.md §1.3)."""

import config

from .navegacao import resolver_itens, url_se_existir


def consus(request):
    return {
        "versao": config.__version__,
        "itens_navegacao": resolver_itens(request),
        "badge_alertas_url": url_se_existir("alertas:contador"),
    }
