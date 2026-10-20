"""Seletores do livro-razão (FR-022, FR-023, FR-025)."""

import datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from apps.movimentacoes.models import Movimentacao
from apps.movimentacoes.selectors import historico_do_produto, listar_movimentacoes
from apps.movimentacoes.services import registrar_movimentacao

pytestmark = pytest.mark.django_db
SP = ZoneInfo("America/Sao_Paulo")


def test_fr022_ordenacao_e_filtros(produto_com_saldo):
    """FR-022/FR-023: -criado_em, -id; filtros por produto e tipo, isolados e combinados."""
    a = produto_com_saldo(nome="A")
    b = produto_com_saldo(nome="B")
    entrada = registrar_movimentacao(produto_id=a.pk, tipo="ENTRADA", quantidade=1)
    lista = list(listar_movimentacoes())
    assert lista[0] == entrada
    assert {m.produto_id for m in listar_movimentacoes(produto_id=b.pk)} == {b.pk}
    assert list(listar_movimentacoes(produto_id=a.pk, tipo="ENTRADA")) == [entrada]


def test_fr023_periodo_inclusivo_no_fuso_local(produto_com_saldo, monkeypatch):
    """FR-023: de/ate inclusivos considerando 00:00 e 23:59 de São Paulo."""
    produto = produto_com_saldo(saldo=0)
    instantes = [
        datetime.datetime(2026, 10, 9, 23, 59, tzinfo=SP),
        datetime.datetime(2026, 10, 10, 0, 0, tzinfo=SP),
        datetime.datetime(2026, 10, 12, 23, 59, tzinfo=SP),
        datetime.datetime(2026, 10, 13, 0, 0, tzinfo=SP),
    ]
    criadas = []
    for instante in instantes:
        monkeypatch.setattr(timezone, "now", lambda instante=instante: instante)
        criadas.append(registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=1))
    resultado = set(
        listar_movimentacoes(
            produto_id=produto.pk,
            de=datetime.date(2026, 10, 10),
            ate=datetime.date(2026, 10, 12),
        )
    )
    assert resultado == {criadas[1], criadas[2]}


def test_fr025_historico_ate_10_mais_recentes(produto_com_saldo):
    """FR-025: histórico do produto limitado às 10 mais recentes."""
    produto = produto_com_saldo(saldo=0)
    for _ in range(11):
        registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=1)
    historico = historico_do_produto(produto.pk)
    assert len(historico) == 10
    assert historico[0] == Movimentacao.objects.filter(produto=produto).first()
