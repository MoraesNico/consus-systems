"""Contador automático no menu (FR-014–FR-017, FR-021)."""

import re

import pytest

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def test_fr014_contador_sem_anterior(client, cenario):
    """FR-014/FR-016: fragmento com polling, evento, ícone, número e texto acessível."""
    resposta = client.get("/alertas/contador/")
    conteudo = html(resposta)
    raiz = re.search(r'<span id="contador-alertas"[^>]*>', conteudo).group(0)
    assert resposta.status_code == 200
    assert 'hx-get="/alertas/contador/?anterior=4"' in raiz
    assert 'hx-trigger="every 30s, estoque-alterado from:body"' in raiz
    assert 'hx-swap="outerHTML"' in raiz and "hidden" not in raiz
    assert "#triangle-alert" in conteudo and ">4<" in conteudo
    assert "produtos em alerta de reposição" in conteudo
    assert "anuncio-alertas" not in conteudo
    assert "no-store" in resposta["Cache-Control"]


def test_fr014_intervalo_configuravel(client, settings, cenario):
    """FR-014: ALERTAS_INTERVALO_SEGUNDOS define o polling."""
    settings.ALERTAS_INTERVALO_SEGUNDOS = 10
    assert 'hx-trigger="every 10s, estoque-alterado from:body"' in html(
        client.get("/alertas/contador/")
    )


def test_fr016_total_zero_fica_oculto(client, criar_produto):
    """FR-016: com zero alertas o elemento existe, vazio e hidden (continua consultando)."""
    criar_produto("Ok", 11, 10)
    conteudo = html(client.get("/alertas/contador/"))
    raiz = re.search(r'<span id="contador-alertas"[^>]*>(.*?)</span>\s*$', conteudo, re.S)
    assert " hidden" in raiz.group(0) and raiz.group(1).strip() == ""


def test_fr017_204_quando_nada_mudou(client, cenario):
    """FR-017: anterior igual ao total → 204 (sem troca nem anúncio repetido)."""
    assert client.get("/alertas/contador/?anterior=4").status_code == 204


def test_fr017_anuncio_quando_muda(client, cenario):
    """FR-017: total diferente → fragmento + anúncio OOB."""
    conteudo = html(client.get("/alertas/contador/?anterior=3"))
    assert re.search(r'<span id="contador-alertas"', conteudo)
    anuncio = re.search(r'<div id="anuncio-alertas" hx-swap-oob="innerHTML">(.*?)</div>', conteudo)
    assert anuncio.group(1).strip() == "Alertas de reposição: 4 produtos (antes 3)."


@pytest.mark.parametrize("anterior", ["", "-1", "abc"])
def test_fr017_anterior_invalido_ignorado(client, cenario, anterior):
    """FR-017: anterior inválido é tratado como ausente."""
    resposta = client.get(f"/alertas/contador/?anterior={anterior}")
    assert resposta.status_code == 200 and "anuncio-alertas" not in html(resposta)


def test_fr002_conta_igual_ao_minimo_e_zero(client, criar_produto):
    """FR-002/FR-003: conta = mínimo e sem estoque; não conta mínimo + 1."""
    criar_produto("Igual", 10, 10)
    criar_produto("Zero", 0, 0)
    criar_produto("Acima", 11, 10)
    assert ">2<" in html(client.get("/alertas/contador/"))


def test_contador_metodos(client):
    """Somente GET."""
    assert client.post("/alertas/contador/").status_code == 405


def test_fr014_tag_dentro_do_badge_em_todas_as_paginas(client, cenario):
    """FR-014: o contador já vem renderizado no menu (funciona sem JS)."""
    for url in ("/", "/produtos/", "/alertas/"):
        conteudo = html(client.get(url))
        slot = re.search(r'<span id="badge-alertas"[^>]*>(.*?)</span>\s*</(?:a|span)>', conteudo,
                         re.S)  # fmt: skip
        assert slot is not None, url
        assert "hx-" not in re.search(r'<span id="badge-alertas"[^>]*>', conteudo).group(0)
        assert 'id="contador-alertas"' in slot.group(1) and ">4<" in slot.group(1)


def test_fr014_sem_rota_a_tag_nao_renderiza(client, settings):
    """FR-014: com urlconf sem alertas:contador, a tag não renderiza nada (testes da 001)."""
    from django.urls import clear_url_caches

    settings.ROOT_URLCONF = "apps.core.tests.urls_core"
    clear_url_caches()
    try:
        conteudo = html(client.get("/"))
    finally:
        clear_url_caches()
    assert 'id="contador-alertas"' not in conteudo
