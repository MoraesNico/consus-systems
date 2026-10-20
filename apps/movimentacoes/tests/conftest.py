"""Fixtures da app movimentacoes."""

import itertools

import pytest

from apps.produtos.services import cadastrar_produto

_sequencia = itertools.count(1)


@pytest.fixture
def produto_com_saldo(db):
    """Produto criado pelo serviço oficial (o saldo vem da movimentação INICIAL)."""

    def criar(nome: str | None = None, saldo: int = 10, minimo: int = 3):
        return cadastrar_produto(
            nome=nome or f"Parafuso {next(_sequencia)}",
            quantidade_inicial=saldo,
            estoque_minimo=minimo,
        )

    return criar


@pytest.fixture
def htmx_alvo():
    def cabecalhos(alvo: str | None = None) -> dict:
        extra = {"HTTP_HX_REQUEST": "true"}
        if alvo:
            extra["HTTP_HX_TARGET"] = alvo
        return extra

    return cabecalhos
