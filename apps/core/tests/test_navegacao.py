"""Navegação principal: ordem, item ativo, itens "em breve" e slot do badge (FR-012–FR-014)."""

import re

import pytest

pytestmark = pytest.mark.django_db


def nav(resposta) -> str:
    conteudo = resposta.content.decode()
    return re.search(r'<nav[^>]*aria-label="Principal".*?</nav>', conteudo, re.S).group(0)


def itens(trecho: str) -> list[str]:
    return re.findall(r'<(?:a|span) class="navegacao__item"[^>]*>.*?</(?:a|span)>', trecho, re.S)


def test_fr012_ordem_e_item_ativo_no_painel(client):
    """FR-012: Painel, Produtos, Movimentações, Financeiro, Alertas; em / só Painel é ativo."""
    trecho = nav(client.get("/"))
    rotulos = [re.sub(r"<[^>]+>|\(em breve\)", "", item).split() for item in itens(trecho)]
    assert [r[0] for r in rotulos] == [
        "Painel",
        "Produtos",
        "Movimentações",
        "Financeiro",
        "Alertas",
    ]
    assert trecho.count('aria-current="page"') == 1
    assert 'aria-current="page"' in itens(trecho)[0]


def test_fr012_item_ativo_por_namespace(client, urls_com_secoes):
    """FR-012: dentro de /produtos/12/ o item Produtos fica ativo."""
    lista = itens(nav(client.get("/produtos/12/")))
    assert 'aria-current="page"' in lista[1]
    assert 'aria-current="page"' not in lista[0]


def test_fr012_catalogo_nao_ativa_itens(client):
    """FR-012: em /design/ nenhum item da navegação fica ativo."""
    assert 'aria-current="page"' not in nav(client.get("/design/"))


def test_fr013_secoes_sem_rota_aparecem_em_breve(client, urls_sem_secoes):
    """FR-013: sem a rota registrada, o item não tem link e mostra "(em breve)"."""
    lista = itens(nav(client.get("/")))
    for item in lista[1:]:
        assert item.startswith("<span")
        assert 'aria-disabled="true"' in item
        assert "(em breve)" in item
        assert "href=" not in item.split(">", 1)[0]


def test_fr013_secoes_com_rota_viram_links(client, urls_com_secoes):
    """FR-013: registrar a rota é suficiente para o item virar link."""
    lista = itens(nav(client.get("/")))
    esperados = ["/produtos/", "/movimentacoes/", "/financeiro/", "/alertas/"]
    for item, url in zip(lista[1:], esperados, strict=True):
        assert item.startswith("<a")
        assert f'href="{url}"' in item
        assert "(em breve)" not in item


def test_fr014_slot_do_badge_vazio_sem_contador(client, urls_sem_secoes):
    """FR-014: sem alertas:contador o slot #badge-alertas fica vazio e sem atributos hx-*."""
    slot = re.search(r'<span id="badge-alertas"[^>]*>(.*?)</span>', nav(client.get("/")), re.S)
    assert slot is not None
    assert "hx-" not in slot.group(0)
    assert slot.group(1).strip() == ""


def test_fr014_slot_do_badge_ligado_ao_contador(client, urls_com_secoes):
    """FR-014: com alertas:contador o slot carrega o contador e escuta estoque-alterado."""
    trecho = nav(client.get("/"))
    slot = trecho.split('id="badge-alertas"', 1)[1].split("</li>", 1)[0]
    assert 'hx-get="/alertas/contador/' in slot
    assert "estoque-alterado from:body" in slot
