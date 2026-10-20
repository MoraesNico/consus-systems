"""Migração 0002: saldo inicial retroativo (FR-030)."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

pytestmark = pytest.mark.django_db(transaction=True)

ANTES = [("movimentacoes", "0001_initial")]
DEPOIS = [("movimentacoes", "0002_saldo_inicial_retroativo")]


def test_fr030_cria_inicial_para_produtos_sem_historico():
    """FR-030: produtos antigos recebem INICIAL = saldo atual (inclusive 0); com histórico, não."""
    executor = MigrationExecutor(connection)
    executor.migrate(ANTES)
    apps = executor.loader.project_state(ANTES).apps
    Produto = apps.get_model("produtos", "Produto")
    Movimentacao = apps.get_model("movimentacoes", "Movimentacao")
    criado = timezone.now() - timezone.timedelta(days=3)
    antigo = Produto.objects.create(nome="Antigo", quantidade_atual=7, estoque_minimo=1)
    Produto.objects.filter(pk=antigo.pk).update(criado_em=criado)
    zerado = Produto.objects.create(nome="Zerado", quantidade_atual=0, estoque_minimo=1)
    com_historico = Produto.objects.create(
        nome="Com histórico", quantidade_atual=5, estoque_minimo=1
    )
    Movimentacao.objects.create(produto=com_historico, tipo="INICIAL", quantidade=5,
                                saldo_anterior=0, saldo_posterior=5)  # fmt: skip

    executor = MigrationExecutor(connection)
    executor.migrate(DEPOIS)
    apps = executor.loader.project_state(DEPOIS).apps
    Movimentacao = apps.get_model("movimentacoes", "Movimentacao")
    inicial = Movimentacao.objects.get(produto_id=antigo.pk)
    assert (inicial.tipo, inicial.quantidade, inicial.saldo_anterior, inicial.saldo_posterior) == (
        "INICIAL", 7, 0, 7)  # fmt: skip
    assert inicial.criado_em == criado
    assert Movimentacao.objects.get(produto_id=zerado.pk).quantidade == 0
    assert Movimentacao.objects.filter(produto_id=com_historico.pk).count() == 1
