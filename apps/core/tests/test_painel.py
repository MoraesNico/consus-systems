"""Painel placeholder da fundação (FR-022)."""

import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("variante", ["normal", "boost", "htmx"])
def test_fr022_painel_com_estado_vazio(client, variante):
    """FR-022: / mostra o Painel com a região de KPIs em estado vazio (página completa)."""
    if variante != "normal":
        client.defaults["HTTP_HX_REQUEST"] = "true"
    if variante == "boost":
        client.defaults["HTTP_HX_BOOSTED"] = "true"
    resposta = client.get("/")
    conteudo = resposta.content.decode()
    assert resposta.status_code == 200
    assert "<html" in conteudo
    assert "<h1" in conteudo and "Painel</h1>" in conteudo
    assert '<section id="painel-kpis"' in conteudo
    assert "Os indicadores aparecem aqui" in conteudo
    assert "Cadastrar produto" in conteudo
    assert "(em breve)" in conteudo.split('id="painel-kpis"', 1)[1]


def test_fr022_acao_vira_link_quando_produtos_existe(client, urls_com_secoes):
    """FR-022: com produtos:novo registrado, a ação aponta para /produtos/novo/."""
    regiao = client.get("/").content.decode().split('id="painel-kpis"', 1)[1]
    assert 'href="/produtos/novo/"' in regiao


def test_fr022_painel_so_aceita_leitura(client):
    """FR-022: POST / → 405."""
    assert client.post("/").status_code == 405
