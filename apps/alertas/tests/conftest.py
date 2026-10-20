"""Fixtures da app alertas."""

import datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from apps.movimentacoes.services import registrar_movimentacao
from apps.produtos.services import cadastrar_produto

AGORA = datetime.datetime(2026, 10, 20, 14, 32, tzinfo=ZoneInfo("America/Sao_Paulo"))


@pytest.fixture
def criar_produto(db):
    def criar(nome: str, quantidade: int, minimo: int):
        return cadastrar_produto(nome=nome, quantidade_inicial=quantidade, estoque_minimo=minimo)

    return criar


@pytest.fixture
def movimentar(db):
    def mover(produto, tipo: str, quantidade: int, observacao: str = ""):
        return registrar_movimentacao(
            produto_id=produto.pk, tipo=tipo, quantidade=quantidade, observacao=observacao
        )

    return mover


@pytest.fixture
def agora(monkeypatch):
    """Fixa o relógio em 20/10/2026 14:32 (São Paulo) para varreduras e painel."""
    monkeypatch.setattr(timezone, "now", lambda: AGORA)
    return AGORA


@pytest.fixture
def htmx():
    return {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def boosted():
    return {"HTTP_HX_REQUEST": "true", "HTTP_HX_BOOSTED": "true"}


@pytest.fixture
def cenario(criar_produto):
    """A (5/10), B (10/10), C (11/10), D (0/8), E (0/20): 3 + 2 sem estoque em alerta."""
    return {
        "A": criar_produto("Arruela lisa 8 mm", 5, 10),
        "B": criar_produto("Bucha 6 mm", 10, 10),
        "C": criar_produto("Cabo flexível 2,5 mm", 11, 10),
        "D": criar_produto("Disjuntor 20 A", 0, 8),
        "E": criar_produto("Eletroduto 3/4", 0, 20),
    }
