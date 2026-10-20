"""Modelo Produto: ID automático, código, restrições do banco e situação (FR-002–FR-006, FR-015)."""

import pytest
from django.db import IntegrityError, transaction

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def criar(nome="Caneta Azul", quantidade_atual=10, estoque_minimo=5) -> Produto:
    return Produto.objects.create(
        nome=nome, quantidade_atual=quantidade_atual, estoque_minimo=estoque_minimo
    )


def test_fr002_id_automatico_crescente_sem_informar():
    """FR-002: o ID é atribuído pelo banco e cresce a cada cadastro."""
    a, b = criar("A"), criar("B")
    assert a.pk is not None and b.pk > a.pk


def test_fr003_codigo_quatro_digitos_sem_truncar():
    """FR-003: código exibido com 4 dígitos, sem truncar IDs maiores."""
    for pk, esperado in ((1, "#0001"), (42, "#0042"), (12345, "#12345")):
        assert Produto(pk=pk).codigo == esperado


def test_str_codigo_e_nome():
    """str(produto) = "#0001 — Nome"."""
    assert str(Produto(pk=1, nome="Caneta Azul")) == "#0001 — Caneta Azul"


def test_fr006_sc006_constraint_quantidade_atual_nao_negativa():
    """FR-006/SC-006: o banco recusa quantidade negativa mesmo por update direto."""
    produto = criar()
    with pytest.raises(IntegrityError), transaction.atomic():
        Produto.objects.filter(pk=produto.pk).update(quantidade_atual=-1)


def test_fr006_constraint_estoque_minimo_nao_negativo():
    """FR-006: o banco recusa estoque mínimo negativo."""
    produto = criar()
    with pytest.raises(IntegrityError), transaction.atomic():
        Produto.objects.filter(pk=produto.pk).update(estoque_minimo=-1)


def test_fr004_constraint_nome_nao_vazio():
    """FR-004: o banco recusa nome vazio."""
    with pytest.raises(IntegrityError), transaction.atomic():
        criar(nome="")


def test_fr005_sc006_unique_lower_nome_no_banco():
    """FR-005/SC-006: "Caneta" e "CANETA" não coexistem no banco."""
    criar("Caneta")
    with pytest.raises(IntegrityError), transaction.atomic():
        criar("CANETA")


@pytest.mark.parametrize(
    ("atual", "minimo", "alerta"),
    [(0, 0, True), (5, 5, True), (4, 5, True), (6, 5, False)],
)
def test_fr015_em_alerta_inclui_igualdade(atual, minimo, alerta):
    """FR-015: quantidade ≤ mínimo está em alerta (inclui igualdade e 0/0)."""
    produto = Produto(quantidade_atual=atual, estoque_minimo=minimo)
    assert produto.em_alerta is alerta
    assert produto.situacao == ("alerta" if alerta else "ok")


def test_fr015_queryset_em_alerta_sem_alerta_com_situacao():
    """FR-015: filtros em_alerta/sem_alerta e anotação `alerta` coerentes com a regra."""
    alerta = criar("Alerta", 5, 5)
    ok = criar("Ok", 6, 5)
    assert list(Produto.objects.em_alerta()) == [alerta]
    assert list(Produto.objects.sem_alerta()) == [ok]
    anotados = {p.pk: p.alerta for p in Produto.objects.com_situacao()}
    assert anotados == {alerta.pk: True, ok.pk: False}


def test_get_absolute_url():
    """O produto aponta para a página de detalhe."""
    assert Produto(pk=7).get_absolute_url() == "/produtos/7/"
