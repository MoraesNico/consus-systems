"""Relatório de reposição /alertas/ (FR-006–FR-013, FR-015, FR-032, FR-033, FR-036)."""

import re

import pytest
from django.template.loader import render_to_string

from apps.alertas.exportacao import para_csv
from apps.alertas.selectors import varrer

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def secao(conteudo: str) -> str:
    return conteudo.split('<section id="relatorio"', 1)[1].split("</section>", 1)[0]


def test_fr007_fr013_pagina_completa(client, cenario, agora):
    """FR-007/FR-013: página com título, varredura sob demanda sem JS e resumo."""
    resposta = client.get("/alertas/")
    conteudo = html(resposta)
    assert resposta.status_code == 200
    assert "alertas/relatorio.html" in [t.name for t in resposta.templates]
    assert "Relatório de reposição" in conteudo
    formulario = re.search(r'<form[^>]*action="/alertas/"[^>]*>', conteudo).group(0)
    assert 'method="get"' in formulario and 'hx-target="#relatorio"' in formulario
    assert "hx-disabled-elt" in formulario
    assert "Executar varredura" in conteudo
    resumo = re.sub(r"<[^>]+>", "", secao(conteudo))
    assert (
        "Varredura em 20/10/2026 14:32 · 5 produtos analisados · 4 em alerta (2 sem estoque)"
        in (re.sub(r"\s+", " ", resumo))
    )


@pytest.mark.parametrize("cabecalho", ["HTTP_HX_BOOSTED", "HTTP_HX_HISTORY_RESTORE_REQUEST"])
def test_boost_e_restauracao_recebem_pagina(client, cenario, cabecalho):
    """Research R8: navegação boostada e restauração de histórico recebem a página inteira."""
    assert "<html" in html(client.get("/alertas/", HTTP_HX_REQUEST="true", **{cabecalho: "true"}))


def test_metodos_e_cabecalhos(client):
    """POST → 405; sem cache; Vary por HX-Request e HX-Target."""
    assert client.post("/alertas/").status_code == 405
    resposta = client.get("/alertas/")
    assert "no-store" in resposta["Cache-Control"]
    assert "HX-Request" in resposta["Vary"] and "HX-Target" in resposta["Vary"]


def test_fr009_conteudo_e_ordem(client, cenario):
    """FR-002/FR-006/FR-009: só os em alerta, na ordem de criticidade, com as colunas."""
    conteudo = secao(html(client.get("/alertas/")))
    ordem = re.findall(r'<tr id="reposicao-(\d+)"', conteudo)
    assert ordem == [str(cenario[k].pk) for k in ("E", "D", "A", "B")]
    assert f'id="reposicao-{cenario["C"].pk}"' not in conteudo
    cabecalho = re.sub(r"<[^>]+>", " ", conteudo.split("<thead", 1)[1].split("</thead>", 1)[0])
    colunas = ["ID", "Produto", "Situação", "Atual", "Mínimo", "Déficit", "Cobertura", "Sugestão"]
    posicoes = [cabecalho.index(c) for c in colunas]
    assert posicoes == sorted(posicoes)
    linha_a = conteudo.split(f'id="reposicao-{cenario["A"].pk}"', 1)[1].split("</tr>", 1)[0]
    assert ">5<" in linha_a and "50%" in linha_a and "+15" in linha_a
    linha_e = conteudo.split(f'id="reposicao-{cenario["E"].pk}"', 1)[1].split("</tr>", 1)[0]
    assert "REPOSIÇÃO NECESSÁRIA" in linha_e and "SEM ESTOQUE" in linha_e
    assert 'id="produto-' not in conteudo


def test_fr036_separador_de_milhar(client, criar_produto):
    """FR-036: quantidades com separador de milhar."""
    criar_produto("Grande", 1200, 5000)
    assert "1.200" in secao(html(client.get("/alertas/")))


def test_fr010_estados_vazios(client, criar_produto):
    """FR-010: sem produtos e sem alertas."""
    vazio = secao(html(client.get("/alertas/")))
    assert "Nenhum produto cadastrado" in vazio and 'href="/produtos/novo/"' in vazio
    criar_produto("Ok", 10, 1)
    criar_produto("Ok 2", 10, 1)
    positivo = secao(html(client.get("/alertas/")))
    assert "Nenhum produto precisa de reposição" in positivo and "2 produtos analisados" in positivo


def test_fr011_acao_rapida_de_entrada(client, criar_produto):
    """FR-011: "+ Entrada" com a sugestão (limitada a 1.000.000) e origem=alertas."""
    a = criar_produto("Arruela", 5, 10)
    grande = criar_produto("Grande", 0, 1_000_000)
    teto = criar_produto("Teto", 2_147_483_647, 2_147_483_647)
    conteudo = secao(html(client.get("/alertas/")))
    linha = conteudo.split(f'id="reposicao-{a.pk}"', 1)[1].split("</tr>", 1)[0]
    assert f'href="/movimentacoes/nova/?produto={a.pk}&amp;tipo=ENTRADA&amp;quantidade=15"' in linha
    assert "origem=alertas" in linha and 'hx-target="#dialogo"' in linha
    assert f'aria-label="Registrar entrada de {a.codigo} Arruela"' in linha
    linha_grande = conteudo.split(f'id="reposicao-{grande.pk}"', 1)[1].split("</tr>", 1)[0]
    assert "quantidade=1000000" in linha_grande
    linha_teto = conteudo.split(f'id="reposicao-{teto.pk}"', 1)[1].split("</tr>", 1)[0]
    assert "quantidade=" not in linha_teto


def test_fr012_fragmento_htmx(client, cenario, htmx):
    """FR-008/FR-012/FR-015: fragmento com auto-recarga, anúncio e contador OOB."""
    conteudo = html(client.get("/alertas/", **htmx))
    assert "<html" not in conteudo
    raiz = re.search(r'<section id="relatorio"[^>]*>', conteudo).group(0)
    assert 'hx-get="/alertas/"' in raiz and 'hx-trigger="estoque-alterado from:body"' in raiz
    assert 'hx-swap="outerHTML"' in raiz
    anuncio = re.search(r'<div id="anuncio-alertas" hx-swap-oob="innerHTML">(.*?)</div>', conteudo)
    assert anuncio.group(1).strip() == (
        "Varredura concluída: 4 produtos em alerta (2 sem estoque) de 5 analisados."
    )
    contador = re.search(r'<span id="contador-alertas"[^>]*>', conteudo).group(0)
    assert 'hx-swap-oob="true"' in contador and "anterior=4" in contador


def test_fr032_csv(client, cenario, agora, htmx):
    """FR-032: ?formato=csv baixa o arquivo, inclusive com HTMX."""
    for extra in ({}, htmx):
        resposta = client.get("/alertas/?formato=csv", **extra)
        assert resposta.status_code == 200
        assert resposta["Content-Type"] == "text/csv; charset=utf-8"
        assert resposta["Content-Disposition"] == (
            'attachment; filename="reposicao-20261020-1432.csv"'
        )
        assert resposta.content.decode() == para_csv(varrer(), bom=True)


def test_fr032_formato_invalido_400(client):
    """FR-032: formato não suportado → 400."""
    resposta = client.get("/alertas/?formato=pdf")
    assert resposta.status_code == 400
    assert resposta.content.decode() == "Formato não suportado. Use html ou csv."


def test_fr032_link_exportar(client):
    """FR-032: link "Exportar CSV" sem boost, com download."""
    link = re.search(r'<a[^>]*href="/alertas/\?formato=csv"[^>]*>', html(client.get("/alertas/")))
    assert 'hx-boost="false"' in link.group(0) and "download" in link.group(0)


def test_navegacao_alertas_ativa_e_regiao_de_anuncio(client):
    """001 FR-012/FR-014: item Alertas vira link ativo; região viva no base.html."""
    conteudo = html(client.get("/alertas/"))
    assert re.search(r'<a class="navegacao__item" href="/alertas/" aria-current="page">', conteudo)
    assert re.search(r'id="anuncio-alertas"[^>]*role="status"[^>]*aria-live="polite"', conteudo)


def test_fr004_fr024_coluna_cobertura(criar_produto):
    """FR-004/FR-009/FR-024: mínimo 0 → "—" sem barra; senão a barra (meter) da 001."""
    sem_minimo = criar_produto("Sem mínimo", 3, 0)
    quarenta = criar_produto("Quarenta", 4, 10)
    acima = criar_produto("Acima", 15, 10)
    itens = {p.pk: p for p in varrer(incluir_ok=True).itens}

    def coluna(produto) -> str:
        linha = render_to_string("alertas/partials/linha_reposicao.html", {"produto": produto})
        return linha.split('class="coluna-cobertura">', 1)[1].split("</td>", 1)[0]

    assert "—" in coluna(itens[sem_minimo.pk]) and "meter" not in coluna(itens[sem_minimo.pk])
    barra = coluna(itens[quarenta.pk])
    assert 'role="meter"' in barra and 'aria-valuenow="40"' in barra
    assert 'aria-valuemax="100"' in barra and "40%" in barra and "tom--reposicao" in barra
    barra = coluna(itens[acima.pk])
    assert "150%" in barra and "--valor: 100" in barra and "tom--ok" in barra
