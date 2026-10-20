"""Comando `movimentar` — paridade de terminal (FR-031)."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def movimentar(*args) -> str:
    saida = StringIO()
    call_command("movimentar", *args, stdout=saida)
    return saida.getvalue()


def test_fr031_entrada_pelo_terminal(produto_com_saldo):
    """FR-031: `movimentar <id> entrada 5` registra e confirma."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    saida = movimentar(str(produto.pk), "entrada", "5")
    assert f"Entrada registrada: {produto.codigo} Parafuso — saldo 10 → 15" in saida


@pytest.mark.parametrize("tipo", ["SAIDA", "saída", "Saida"])
def test_fr031_aceita_codigo_e_variacoes_de_tipo(produto_com_saldo, tipo):
    """FR-031: aceita #0001 e saída com/sem acento, maiúsculas ou minúsculas."""
    produto = produto_com_saldo(saldo=10)
    movimentar(produto.codigo, tipo, "3", "--obs", "Venda balcão")
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 7
    assert produto.movimentacoes.first().observacao == "Venda balcão"


def test_fr031_saldo_insuficiente_vira_erro_de_comando(produto_com_saldo):
    """FR-031/FR-004: saldo insuficiente → CommandError sem gravar."""
    produto = produto_com_saldo(saldo=7)
    with pytest.raises(CommandError, match="Saldo insuficiente: disponível 7, solicitado 50"):
        movimentar(str(produto.pk), "saida", "50")
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 7


@pytest.mark.parametrize(
    "args",
    [("99999", "entrada", "1"), ("{pk}", "inicial", "1"), ("{pk}", "troca", "1"),
     ("{pk}", "entrada", "2,5"), ("{pk}", "entrada", "0"),
     ("{pk}", "entrada", "1", "--obs", "x" * 201)],
)  # fmt: skip
def test_fr031_entradas_invalidas(produto_com_saldo, args):
    """FR-031/FR-005/FR-006: entradas inválidas → CommandError sem gravar."""
    produto = produto_com_saldo(saldo=10)
    with pytest.raises(CommandError):
        movimentar(*[a.format(pk=produto.pk) for a in args])
    assert produto.movimentacoes.count() == 1
