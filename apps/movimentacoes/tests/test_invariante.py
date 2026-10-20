"""Invariante do livro-razão: saldo = Σ movimentações (FR-028, FR-029, SC-004)."""

import random

import pytest

from apps.movimentacoes.selectors import auditar_saldos
from apps.movimentacoes.services import MovimentacaoError, registrar_movimentacao
from apps.produtos.models import Produto
from apps.produtos.services import cadastrar_produto

pytestmark = pytest.mark.django_db


def test_sc004_sequencia_aleatoria_mantem_invariante():
    """SC-004: após centenas de operações (com recusas), o livro-razão fecha."""
    sorteio = random.Random(20261020)
    produtos = [
        cadastrar_produto(nome=f"P{i}", quantidade_inicial=sorteio.randint(0, 50), estoque_minimo=5)
        for i in range(6)
    ]
    recusas = 0
    for _ in range(300):
        produto = sorteio.choice(produtos)
        tipo = sorteio.choice(["ENTRADA", "SAIDA", "SAIDA"])
        try:
            registrar_movimentacao(
                produto_id=produto.pk, tipo=tipo, quantidade=sorteio.randint(1, 30)
            )
        except MovimentacaoError:
            recusas += 1
    assert recusas > 0
    assert auditar_saldos() == []
    for produto in Produto.objects.all():
        movs = list(produto.movimentacoes.order_by("criado_em", "id"))
        soma = sum(m.quantidade if m.tipo != "SAIDA" else -m.quantidade for m in movs)
        assert soma == produto.quantidade_atual >= 0
        assert movs[0].tipo == "INICIAL" and sum(m.tipo == "INICIAL" for m in movs) == 1
        for anterior, seguinte in zip(movs, movs[1:], strict=False):
            assert anterior.saldo_posterior == seguinte.saldo_anterior


def test_fr029_auditoria_aponta_divergencia_fabricada():
    """FR-029: uma alteração direta de saldo é denunciada pela auditoria."""
    produto = cadastrar_produto(nome="Fraude", quantidade_inicial=10, estoque_minimo=1)
    Produto.objects.filter(pk=produto.pk).update(quantidade_atual=99)
    divergencias = auditar_saldos()
    assert len(divergencias) == 1
    assert divergencias[0].produto_id == produto.pk and divergencias[0].motivo == "soma"
    assert (divergencias[0].saldo_atual, divergencias[0].saldo_calculado) == (99, 10)
