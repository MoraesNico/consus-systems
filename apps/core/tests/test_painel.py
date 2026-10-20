"""Painel da fundação (FR-022 da 001), com o conteúdo entregue pela 004."""

import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("variante", ["normal", "boost"])
def test_fr022_painel_pagina_completa_sem_secoes(client, urls_sem_secoes, variante):
    """FR-022: / mostra o Painel com a região #painel-kpis; sem produtos convida a cadastrar."""
    if variante == "boost":
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.defaults["HTTP_HX_BOOSTED"] = "true"
    resposta = client.get("/")
    conteudo = resposta.content.decode()
    assert resposta.status_code == 200
    assert "<html" in conteudo
    assert "<h1" in conteudo and "Painel</h1>" in conteudo
    assert '<section id="painel-kpis"' in conteudo
    regiao = conteudo.split('id="painel-kpis"', 1)[1]
    assert "Cadastre o primeiro produto" in regiao
    assert "(em breve)" in regiao


def test_fr022_painel_fragmento_htmx(client):
    """FR-022 (004): requisição HTMX parcial recebe só a região #painel-kpis."""
    conteudo = client.get("/", HTTP_HX_REQUEST="true").content.decode()
    assert conteudo.lstrip().startswith('<section id="painel-kpis"') and "<html" not in conteudo


def test_fr022_acao_vira_link_quando_produtos_existe(client, urls_com_secoes):
    """FR-022: com produtos:novo registrado, a ação aponta para /produtos/novo/."""
    regiao = client.get("/").content.decode().split('id="painel-kpis"', 1)[1]
    assert 'href="/produtos/novo/"' in regiao


def test_fr022_painel_so_aceita_leitura(client):
    """FR-022: POST / → 405."""
    assert client.post("/").status_code == 405
