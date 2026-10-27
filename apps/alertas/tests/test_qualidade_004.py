"""Concordância entre superfícies, acessibilidade estrutural e volume (SC-001, SC-005–SC-007)."""

import json
import re
from io import StringIO

import pytest
from django.core.management import call_command

from apps.alertas.exportacao import para_csv
from apps.alertas.selectors import varrer
from apps.movimentacoes.models import Movimentacao
from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db

LIMITES = {  # nome: (quantidade, mínimo, rótulo esperado)
    "Abaixo": (4, 5, "REPOSIÇÃO NECESSÁRIA"),
    "Igual": (5, 5, "REPOSIÇÃO NECESSÁRIA"),
    "Mais um": (6, 5, "OK"),
    "Zero com mínimo": (0, 5, "SEM ESTOQUE"),
    "Zero sem mínimo": (0, 0, "SEM ESTOQUE"),
}


def test_sc001_sc006_mesma_situacao_em_todas_as_superficies(client, criar_produto):
    """SC-001/SC-006: relatório, contador, lista, JSON e CSV concordam nos 5 limites."""
    produtos = {nome: criar_produto(nome, q, m) for nome, (q, m, _) in LIMITES.items()}
    relatorio = client.get("/alertas/").content.decode()
    lista = client.get("/produtos/").content.decode()
    saida = StringIO()
    call_command("varrer_estoque", "--formato", "json", "--todos", stdout=saida)
    itens_json = {i["nome"]: i["situacao_rotulo"] for i in json.loads(saida.getvalue())["itens"]}
    csv = para_csv(varrer(), bom=False)
    for nome, (_, _, rotulo) in LIMITES.items():
        produto = produtos[nome]
        em_alerta = rotulo != "OK"
        assert itens_json[nome] == rotulo
        assert (f'id="reposicao-{produto.pk}"' in relatorio) is em_alerta
        assert (f";{rotulo}\r\n" in csv and nome in csv) is em_alerta
        linha = lista.split(f'id="produto-{produto.pk}"', 1)[1].split("</tr>", 1)[0]
        assert ("REPOSIÇÃO NECESSÁRIA" in linha) is em_alerta
        assert ("SEM ESTOQUE" in linha) is (rotulo == "SEM ESTOQUE")
    contador = client.get("/alertas/contador/").content.decode()
    assert re.search(r'class="contador-alertas__numero">4<', contador)


def test_sc007_acessibilidade_estrutural(client, criar_produto):
    """SC-007/FR-021: todo alerta tem ícone aria-hidden E texto; tabela com caption e scope."""
    criar_produto("Alerta", 1, 5)
    criar_produto("Zerado", 0, 5)
    for url in ("/alertas/", "/produtos/", "/"):
        conteudo = client.get(url).content.decode()
        for selo in re.findall(r'<span class="badge badge--reposicao">.*?</span>', conteudo):
            assert 'aria-hidden="true"' in selo and "REPOSIÇÃO NECESSÁRIA" in selo
    relatorio = client.get("/alertas/").content.decode()
    assert "<caption" in relatorio and relatorio.count('scope="col"') >= 8
    assert re.search(r'<a[^>]+aria-label="Registrar entrada de #\d+ Alerta"', relatorio)
    assert re.search(r'id="anuncio-alertas"[^>]*role="status"[^>]*aria-live="polite"', relatorio)


def test_sc005_volume_de_mil_produtos(client, django_assert_max_num_queries):
    """SC-005: 1.000 produtos — relatório ≤ 3 consultas, contador 1, painel ≤ 7."""
    produtos = Produto.objects.bulk_create(
        Produto(nome=f"Volume {i:04d}", quantidade_atual=i % 20, estoque_minimo=10)
        for i in range(1000)
    )
    Movimentacao.objects.bulk_create(
        Movimentacao(produto=p, tipo="INICIAL", quantidade=p.quantidade_atual, saldo_anterior=0,
                     saldo_posterior=p.quantidade_atual)
        for p in produtos
    )  # fmt: skip
    assert len(varrer().itens) == 550
    with django_assert_max_num_queries(3):
        client.get("/alertas/", HTTP_HX_REQUEST="true")
    with django_assert_max_num_queries(1):
        client.get("/alertas/contador/")
    with django_assert_max_num_queries(9):
        client.get("/")
