"""Fixtures da app produtos."""

import itertools

import pytest

from apps.produtos.services import cadastrar_produto

_sequencia = itertools.count(1)


@pytest.fixture
def produto_factory(db):
    """Cria produtos pelo serviço oficial (nunca gravando quantidade diretamente)."""

    def criar(nome: str | None = None, quantidade_inicial: int = 10, estoque_minimo: int = 5):
        return cadastrar_produto(
            nome=nome or f"Produto de teste {next(_sequencia)}",
            quantidade_inicial=quantidade_inicial,
            estoque_minimo=estoque_minimo,
        )

    return criar


@pytest.fixture
def hx_parcial():
    def cabecalhos(alvo: str, url_atual: str = "http://testserver/produtos/") -> dict:
        return {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": alvo, "HTTP_HX_CURRENT_URL": url_atual}

    return cabecalhos


@pytest.fixture
def hx_boosted():
    return {"HTTP_HX_REQUEST": "true", "HTTP_HX_BOOSTED": "true"}
