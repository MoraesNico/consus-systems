"""ProdutoQuerySet com as anotações da 004 (FR-001, FR-002, FR-004 da 004; research R2)."""

import pytest

from apps.movimentacoes.services import registrar_movimentacao
from apps.produtos.models import QUANTIDADE_MAXIMA, Produto
from apps.produtos.services import cadastrar_produto, editar_produto

pytestmark = pytest.mark.django_db


def criar(nome, quantidade, minimo):
    return cadastrar_produto(nome=nome, quantidade_inicial=quantidade, estoque_minimo=minimo)


def test_em_alerta_inclui_igualdade_e_zero():
    """FR-002: igual ao mínimo e 0/0 entram; mínimo + 1 não."""
    igual, zero, acima = criar("Igual", 10, 10), criar("Zero", 0, 0), criar("Acima", 11, 10)
    ids = set(Produto.objects.em_alerta().values_list("id", flat=True))
    assert ids == {igual.pk, zero.pk} and acima.pk not in ids


def test_com_situacao_anota_sem_filtrar():
    """FR-001/FR-004: anotações alerta, deficit e cobertura_percentual sem filtrar nem reordenar."""
    a, b, c = criar("A", 5, 10), criar("B", 3, 0), criar("C", 0, 8)
    anotados = {p.pk: p for p in Produto.objects.com_situacao()}
    assert len(anotados) == 3
    assert (anotados[a.pk].alerta, anotados[a.pk].deficit, anotados[a.pk].cobertura_percentual) == (
        True, 5, 50)  # fmt: skip
    assert anotados[b.pk].cobertura_percentual is None and anotados[b.pk].deficit == 0
    assert anotados[c.pk].cobertura_percentual == 0 and anotados[c.pk].deficit == 8


def test_r2_valores_extremos_sem_estouro():
    """Research R2: aritmética em bigint (sem integer out of range no PostgreSQL)."""
    criar("Teto", QUANTIDADE_MAXIMA, QUANTIDADE_MAXIMA)
    criar("Muito", 30_000_000, 1)
    cobertura = {p.nome: p.cobertura_percentual for p in Produto.objects.com_situacao()}
    assert cobertura == {"Teto": 100, "Muito": 3_000_000_000}


def test_situacao_muda_apos_movimentar_e_editar_minimo():
    """FR-001: a situação é derivada — muda com movimentação e com edição do mínimo."""
    produto = criar("Derivada", 11, 10)
    assert not Produto.objects.com_situacao().get(pk=produto.pk).alerta
    registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=1)
    assert Produto.objects.com_situacao().get(pk=produto.pk).alerta
    editar_produto(produto_id=produto.pk, nome="Derivada", estoque_minimo=5)
    assert not Produto.objects.com_situacao().get(pk=produto.pk).alerta
    campos = {f.name for f in Produto._meta.get_fields()}
    assert not campos & {"alerta", "deficit", "cobertura_percentual", "situacao"}
    assert not hasattr(Produto, "deficit") and not hasattr(Produto, "cobertura_percentual")
