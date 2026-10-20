"""Detalhe do produto (FR-021, FR-022, FR-023, FR-026)."""

import pytest
from django.utils import timezone

from apps.produtos.models import Produto

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def test_fr021_detalhe_exibe_dados_e_datas(client, produto_factory):
    """FR-021: código, nome, quantidade com milhar, mínimo, situação e datas dd/mm/aaaa HH:MM."""
    produto = produto_factory(nome="Parafuso M8", quantidade_inicial=1240, estoque_minimo=200)
    conteudo = html(client.get(f"/produtos/{produto.pk}/"))
    criado = timezone.localtime(produto.criado_em).strftime("%d/%m/%Y %H:%M")
    for trecho in (produto.codigo, "Parafuso M8", "1.240", "200", "OK", criado):
        assert trecho in conteudo, trecho


@pytest.mark.parametrize("boost", [False, True])
def test_fr021_detalhe_comum_e_boosted_200(client, produto_factory, hx_boosted, boost):
    """FR-021: detalhe responde 200 com o template de página."""
    produto = produto_factory()
    resposta = client.get(f"/produtos/{produto.pk}/", **(hx_boosted if boost else {}))
    assert resposta.status_code == 200
    assert "produtos/detalhe.html" in [t.name for t in resposta.templates]


def test_fr022_regiao_historico_reservada(client, produto_factory):
    """FR-022: a região de histórico (feature 003) existe no detalhe."""
    produto = produto_factory()
    conteudo = html(client.get(f"/produtos/{produto.pk}/"))
    assert f'id="produto-{produto.pk}-historico"' in conteudo
    assert f'id="produto-{produto.pk}-resumo"' in conteudo


def test_fr023_produto_inexistente_404_com_link_para_lista(client):
    """FR-023: produto inexistente → 404 com link de volta para a lista."""
    resposta = client.get("/produtos/999/")
    assert resposta.status_code == 404
    assert "produtos/nao_encontrado.html" in [t.name for t in resposta.templates]
    assert 'href="/produtos/"' in html(resposta)


def test_fr023_id_acima_do_bigint_404(client):
    """FR-023: ID acima do BigAutoField → 404 (sem erro 500)."""
    assert client.get(f"/produtos/{10**25}/").status_code == 404


def test_fr026_post_e_delete_no_detalhe_405_produto_permanece(client, produto_factory):
    """FR-026: não há exclusão de produto."""
    produto = produto_factory()
    assert client.post(f"/produtos/{produto.pk}/").status_code == 405
    assert client.delete(f"/produtos/{produto.pk}/").status_code == 405
    assert Produto.objects.filter(pk=produto.pk).exists()
