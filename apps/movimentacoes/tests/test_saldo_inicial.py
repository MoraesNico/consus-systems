"""Quantidade Inicial vira a movimentação INICIAL (FR-027, FR-028)."""

import pytest

from apps.movimentacoes import services as servicos_mov
from apps.movimentacoes.forms import MovimentacaoForm
from apps.movimentacoes.services import MovimentacaoInvalidaError, registrar_movimentacao
from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("quantidade", [10, 0])
def test_fr027_cadastro_gera_inicial(quantidade):
    """FR-027: o cadastro cria exatamente um INICIAL 0 → quantidade (inclusive 0)."""
    produto = cadastrar_produto(nome="Parafuso", quantidade_inicial=quantidade, estoque_minimo=1)
    inicial = produto.movimentacoes.get()
    assert (inicial.tipo, inicial.saldo_anterior, inicial.saldo_posterior) == (
        "INICIAL",
        0,
        quantidade,
    )
    assert produto.quantidade_atual == quantidade


def test_fr027_falha_no_inicial_desfaz_o_cadastro(monkeypatch):
    """FR-027: se o INICIAL falhar, nem produto nem movimentação ficam gravados."""

    def falhar(**kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(servicos_mov, "registrar_movimentacao", falhar)
    with pytest.raises(RuntimeError):
        cadastrar_produto(nome="Parafuso", quantidade_inicial=5, estoque_minimo=1)
    assert Produto.objects.count() == 0


def test_fr028_inicial_so_uma_vez():
    """FR-028: INICIAL em produto com histórico é recusado."""
    produto = cadastrar_produto(nome="Parafuso", quantidade_inicial=0, estoque_minimo=1)
    with pytest.raises(
        MovimentacaoInvalidaError, match=f"Saldo inicial já registrado para {produto.codigo}."
    ):
        registrar_movimentacao(produto_id=produto.pk, tipo="INICIAL", quantidade=3)


def test_fr028_formulario_nunca_oferece_saldo_inicial():
    """FR-028: "Saldo inicial" não é opção de tipo no formulário."""
    assert "Saldo inicial" not in str(MovimentacaoForm()["tipo"])
