"""Edição de nome e estoque mínimo (FR-023–FR-027, FR-031)."""

import re

import pytest

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


@pytest.mark.parametrize("boost", [False, True])
def test_fr024_get_editar_preenchido_comum_e_boosted(client, produto_factory, hx_boosted, boost):
    """FR-024: formulário preenchido; quantidade só leitura com a nota; sem campo de quantidade."""
    produto = produto_factory(nome="Caneta", quantidade_inicial=1240, estoque_minimo=7)
    resposta = client.get(f"/produtos/{produto.pk}/editar/", **(hx_boosted if boost else {}))
    conteudo = html(resposta)
    assert resposta.status_code == 200
    assert re.search(r'<input[^>]+name="nome"[^>]+value="Caneta"', conteudo)
    assert re.search(r'<input[^>]+name="estoque_minimo"[^>]+value="7"', conteudo)
    assert "1.240" in conteudo and "Muda apenas por movimentação" in conteudo
    assert 'name="quantidade_atual"' not in conteudo


@pytest.mark.parametrize("boost", [False, True])
def test_fr027_post_valido_302_detalhe_com_mensagem(client, produto_factory, hx_boosted, boost):
    """FR-027: válido → 302 para o detalhe com "Produto #0001 atualizado"."""
    produto = produto_factory(nome="Caneta")
    extra = hx_boosted if boost else {}
    resposta = client.post(f"/produtos/{produto.pk}/editar/",
                           {"nome": "Caneta Preta", "estoque_minimo": "3"}, **extra)  # fmt: skip
    assert resposta.status_code == 302 and resposta["Location"] == f"/produtos/{produto.pk}/"
    detalhe = html(client.get(resposta["Location"], **extra))
    assert f"Produto {produto.codigo} atualizado" in detalhe and "Caneta Preta" in detalhe


def test_fr027_situacao_recalculada_apos_mudar_minimo(client, produto_factory):
    """FR-027: aumentar o mínimo pode colocar o produto em alerta."""
    produto = produto_factory(quantidade_inicial=10, estoque_minimo=5)
    client.post(f"/produtos/{produto.pk}/editar/", {"nome": produto.nome, "estoque_minimo": "10"})
    assert "REPOSIÇÃO NECESSÁRIA" in html(client.get(f"/produtos/{produto.pk}/"))


def test_fr031_edicao_boosted_rerenderiza_pagina_completa(client, produto_factory, hx_boosted):
    """FR-031: após editar com boost, o layout inteiro (com o contador) é re-renderizado."""
    produto = produto_factory()
    resposta = client.post(f"/produtos/{produto.pk}/editar/",
                           {"nome": produto.nome, "estoque_minimo": "1"}, follow=True,
                           **hx_boosted)  # fmt: skip
    assert "<html" in html(resposta) and 'id="badge-alertas"' in html(resposta)


def test_fr025_post_adulterado_quantidade_ignorada(client, produto_factory):
    """FR-025: campos extras (quantidade) enviados à edição são ignorados."""
    produto = produto_factory(quantidade_inicial=10)
    client.post(f"/produtos/{produto.pk}/editar/",
                {"nome": produto.nome, "estoque_minimo": "2", "quantidade_atual": "999",
                 "quantidade_inicial": "999"})  # fmt: skip
    assert Produto.objects.get(pk=produto.pk).quantidade_atual == 10


@pytest.mark.parametrize(
    "dados",
    [{"nome": "Outro", "estoque_minimo": "1"}, {"nome": "", "estoque_minimo": "1"},
     {"nome": "Ok", "estoque_minimo": "-1"}],
)  # fmt: skip
def test_fr024_post_invalido_422(client, produto_factory, dados):
    """FR-024: duplicado, vazio ou negativo → 422."""
    produto_factory(nome="Outro")
    produto = produto_factory(nome="Caneta")
    resposta = client.post(f"/produtos/{produto.pk}/editar/", dados)
    assert resposta.status_code == 422
    assert Produto.objects.get(pk=produto.pk).nome == "Caneta"


def test_fr023_editar_inexistente_404(client):
    """FR-023: editar produto inexistente → 404."""
    assert client.get("/produtos/999/editar/").status_code == 404
    assert (
        client.post("/produtos/999/editar/", {"nome": "X", "estoque_minimo": "1"}).status_code
        == 404
    )


def test_fr026_nenhuma_acao_de_excluir(client, produto_factory):
    """FR-026: lista, detalhe e edição não oferecem exclusão."""
    produto = produto_factory()
    for url in ("/produtos/", f"/produtos/{produto.pk}/", f"/produtos/{produto.pk}/editar/"):
        conteudo = html(client.get(url))
        assert "Excluir" not in conteudo and 'method="delete"' not in conteudo.lower()
