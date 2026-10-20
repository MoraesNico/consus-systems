"""Livro-razão com 100.000 movimentações no PostgreSQL (SC-007)."""

import time

import pytest
from django.utils import timezone

from apps.movimentacoes.models import Movimentacao
from apps.produtos.models import Produto

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


def test_sc007_primeira_pagina_rapida_com_100_mil(client, django_assert_max_num_queries):
    """SC-007: primeira página < 1 s; fragmento com no máximo 5 consultas."""
    produtos = Produto.objects.bulk_create(
        Produto(nome=f"Carga {i}", quantidade_atual=999, estoque_minimo=1) for i in range(100)
    )
    agora = timezone.now()
    movimentos = []
    for produto in produtos:
        inicial = Movimentacao(produto=produto, tipo="INICIAL", quantidade=0, saldo_anterior=0,
                               saldo_posterior=0, criado_em=agora)  # fmt: skip
        movimentos.append(inicial)
        movimentos.extend(
            Movimentacao(
                produto=produto,
                tipo="ENTRADA",
                quantidade=1,
                saldo_anterior=i,
                saldo_posterior=i + 1,
                criado_em=agora,
            )  # fmt: skip
            for i in range(999)
        )
    Movimentacao.objects.bulk_create(movimentos, batch_size=5000)
    assert Movimentacao.objects.count() == 100_000
    for url in ("/movimentacoes/", f"/movimentacoes/?produto={produtos[0].pk}"):
        inicio = time.monotonic()
        assert client.get(url).status_code == 200
        assert time.monotonic() - inicio < 1.0, url
    with django_assert_max_num_queries(5):
        client.get("/movimentacoes/", HTTP_HX_REQUEST="true", HTTP_HX_TARGET="resultados")
