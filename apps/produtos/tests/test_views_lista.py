"""Lista de produtos: colunas, situação, busca, filtros, ordenação e paginação (FR-012–FR-020)."""

import re
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def linhas(conteudo: str) -> list[str]:
    return re.findall(r'<tr id="produto-(\d+)"', conteudo)


def test_fr012_colunas_e_formatos(client, produto_factory):
    """FR-012: colunas ID, Nome, Quantidade atual, Estoque mínimo, Situação; milhar com ponto."""
    produto = produto_factory(nome="Parafuso", quantidade_inicial=1500, estoque_minimo=200)
    conteudo = html(client.get("/produtos/"))
    cabecalho = re.sub(r"<[^>]+>", " ", conteudo.split("<thead", 1)[1].split("</thead>", 1)[0])
    for coluna in ("ID", "Nome", "Quantidade atual", "Estoque mínimo", "Situação"):
        assert coluna in cabecalho, coluna
    assert produto.codigo in conteudo and "1.500" in conteudo


def test_fr003_lista_exibe_codigo(client, produto_factory):
    """FR-003: a lista mostra o código #0001."""
    produto = produto_factory()
    assert f">{produto.codigo}<" in html(client.get("/produtos/"))


def test_fr020_situacao_alerta_icone_e_texto(client, produto_factory):
    """FR-020: alerta com ícone + REPOSIÇÃO NECESSÁRIA; ok com "OK"."""
    alerta = produto_factory(quantidade_inicial=3, estoque_minimo=5)
    ok = produto_factory(quantidade_inicial=30, estoque_minimo=5)
    conteudo = html(client.get("/produtos/"))
    linha_alerta = conteudo.split(f'id="produto-{alerta.pk}"', 1)[1].split("</tr>", 1)[0]
    linha_ok = conteudo.split(f'id="produto-{ok.pk}"', 1)[1].split("</tr>", 1)[0]
    assert "REPOSIÇÃO NECESSÁRIA" in linha_alerta and "<svg" in linha_alerta
    assert ">OK<" in re.sub(r"<svg.*?</svg>", "", linha_ok)


def test_fr016_ordem_padrao_id_decrescente(client, produto_factory):
    """FR-016: padrão = mais recente no topo."""
    a, b = produto_factory(), produto_factory()
    assert linhas(html(client.get("/produtos/")))[:2] == [str(b.pk), str(a.pk)]


def test_fr019_estado_vazio_sem_produtos(client):
    """FR-019: sem produtos → estado vazio com ação de cadastrar (página e diálogo)."""
    conteudo = html(client.get("/produtos/"))
    assert "Nenhum produto cadastrado" in conteudo
    acao = re.search(r'<a[^>]*href="/produtos/novo/"[^>]*>[^<]*(?:<[^>]+>[^<]*)*Cadastrar produto',
                     conteudo.split("Nenhum produto cadastrado", 1)[1]).group(0)  # fmt: skip
    assert 'hx-get="/produtos/novo/"' in acao and 'hx-target="#dialogo"' in acao
    assert "<thead" not in conteudo


def test_fr010_destaque_consumido_da_sessao(client, produto_factory):
    """FR-010: o destaque vem da sessão e é consumido na primeira exibição."""
    produto = produto_factory()
    sessao = client.session
    sessao["produtos_destaque"] = produto.pk
    sessao.save()
    assert "tabela__linha--destaque" in html(client.get("/produtos/"))
    assert "produtos_destaque" not in client.session
    assert "tabela__linha--destaque" not in html(client.get("/produtos/"))


# ---------- Busca, filtros e paginação (US2) ----------


def test_fr014_parcial_hx_target_resultados(client, produto_factory, hx_parcial):
    """FR-014: HX-Target resultados → só o fragmento + contagem OOB."""
    produto_factory()
    conteudo = html(client.get("/produtos/?q=Produto", **hx_parcial("resultados")))
    assert conteudo.lstrip().startswith('<div id="resultados"')
    assert "<html" not in conteudo
    assert re.search(r'id="contagem-produtos"[^>]*hx-swap-oob="true"', conteudo)


@pytest.mark.parametrize("cabecalho", ["HTTP_HX_BOOSTED", "HTTP_HX_HISTORY_RESTORE_REQUEST"])
def test_fr014_boosted_e_restauracao_retornam_pagina_completa(client, cabecalho):
    """FR-014: navegação boostada e restauração de histórico recebem a página inteira."""
    resposta = client.get("/produtos/", HTTP_HX_REQUEST="true", **{cabecalho: "true"},
                          HTTP_HX_TARGET="resultados")  # fmt: skip
    assert "<html" in html(resposta)


def test_fr014_busca_sem_js_formulario_get(client):
    """FR-014: sem JS a busca é um formulário GET com botão Buscar."""
    conteudo = html(client.get("/produtos/"))
    formulario = re.search(r'<form id="filtros-produtos"[^>]*>', conteudo).group(0)
    assert 'method="get"' in formulario and 'role="search"' in formulario
    assert re.search(r"<button[^>]*type=\"submit\"[^>]*>[^<]*Buscar", conteudo)


def test_fr014_indica_atualizacao_e_anuncia_contagem(client, produto_factory):
    """FR-014: a busca indica atualização em #resultados e a contagem é role=status."""
    produto_factory()
    conteudo = html(client.get("/produtos/"))
    busca = re.search(r'<input[^>]+name="q"[^>]*>', conteudo).group(0)
    assert 'hx-indicator="#resultados"' in busca
    assert 'hx-trigger="input changed delay:300ms, search"' in busca
    assert re.search(r'<p id="contagem-produtos"[^>]*role="status"', conteudo)


def test_fr018_hx_push_url_canonica(client, produto_factory, hx_parcial):
    """FR-018: HX-Push-Url sem parâmetros vazios ou padrão."""
    produto_factory()
    resposta = client.get("/produtos/?q=&situacao=alerta&ordem=-id&pagina=1",
                          **hx_parcial("resultados"))  # fmt: skip
    assert resposta["HX-Push-Url"] == "/produtos/?situacao=alerta"
    vazia = client.get("/produtos/?q=+&ordem=xyz", **hx_parcial("resultados"))
    assert vazia["HX-Push-Url"] == "/produtos/"


def test_fr018_vary_hx_request_hx_target(client):
    """FR-018: a lista varia por HX-Request e HX-Target (cache do navegador seguro)."""
    vary = client.get("/produtos/")["Vary"]
    assert "HX-Request" in vary and "HX-Target" in vary


def test_fr018_mesma_url_mesmo_resultado(client, produto_factory, hx_parcial):
    """FR-018: página completa e parcial com os mesmos parâmetros listam as mesmas linhas."""
    for i in range(30):
        produto_factory(nome=f"Peça {i}", quantidade_inicial=i, estoque_minimo=10)
    url = "/produtos/?q=Peça&situacao=alerta&ordem=nome&pagina=1"
    assert linhas(html(client.get(url))) == linhas(
        html(client.get(url, **hx_parcial("resultados")))
    )


def test_fr017_paginacao_25_e_indicador(client, produto_factory):
    """FR-017: 25 por página, indicador "1–25 de 60", ajustes de página e links com filtros."""
    for i in range(60):
        produto_factory(nome=f"Item {i:03d}")
    pagina1 = html(client.get("/produtos/"))
    assert len(linhas(pagina1)) == 25
    assert "1–25 de 60" in re.sub(r"<[^>]+>", "", pagina1)
    assert len(linhas(html(client.get("/produtos/?pagina=3")))) == 10
    assert linhas(html(client.get("/produtos/?pagina=999"))) == linhas(
        html(client.get("/produtos/?pagina=3"))
    )
    assert linhas(html(client.get("/produtos/?pagina=abc"))) == linhas(pagina1)
    filtrada = html(client.get("/produtos/?q=Item&situacao=ok&ordem=nome"))
    proxima = re.search(r'href="(\?[^"]*pagina=2[^"]*)"', filtrada).group(1).replace("&amp;", "&")
    parametros = parse_qs(urlparse(proxima).query)
    assert parametros["q"] == ["Item"] and parametros["situacao"] == ["ok"]
    assert parametros["ordem"] == ["nome"]


def test_fr016_cabecalhos_aria_sort_e_links(client, produto_factory):
    """FR-016: cabeçalhos ordenáveis com aria-sort e links que invertem a ordem."""
    produto_factory()
    conteudo = html(client.get("/produtos/?ordem=nome"))
    th_nome = re.search(r'<th[^>]*aria-sort="ascending"[^>]*>.*?</th>', conteudo, re.S).group(0)
    assert "Nome" in th_nome and "ordem=-nome" in th_nome
    assert 'hx-target="#resultados"' in th_nome and 'hx-push-url="true"' in th_nome
    assert conteudo.count('aria-sort="none"') >= 3


def test_fr015_select_situacao_opcoes(client):
    """FR-015: o filtro de situação oferece Todos, Em alerta e OK."""
    conteudo = html(client.get("/produtos/?situacao=alerta"))
    select = re.search(r'<select[^>]+name="situacao".*?</select>', conteudo, re.S).group(0)
    assert ">Todos<" in select and ">Em alerta<" in select and ">OK<" in select
    assert re.search(r'<option value="alerta" selected>', select)


def test_fr019_nenhum_produto_encontrado_cita_termo_e_limpar_busca(client, produto_factory):
    """FR-019: busca sem resultado cita o termo e oferece "Limpar busca"."""
    produto_factory()
    conteudo = html(client.get("/produtos/?q=inexistente"))
    assert "Nenhum produto encontrado" in conteudo and "inexistente" in conteudo
    assert re.search(r'<a[^>]*href="/produtos/"[^>]*>\s*Limpar busca', conteudo)


def test_fr012_id_e_nome_levam_ao_detalhe(client, produto_factory):
    """FR-012: código e nome são links para o detalhe."""
    produto = produto_factory(nome="Caneta")
    linha = html(client.get("/produtos/")).split(f'id="produto-{produto.pk}"', 1)[1]
    assert linha.count(f'href="/produtos/{produto.pk}/"') >= 2


def test_sc003_lista_consultas_limitadas(client, produto_factory, django_assert_max_num_queries):
    """SC-003: no máximo 4 consultas por requisição da lista, com 60 produtos."""
    for _ in range(60):
        produto_factory()
    with django_assert_max_num_queries(6):  # +2 da sessão autenticada (006)
        client.get("/produtos/?q=Produto&situacao=ok&ordem=nome&pagina=2")
