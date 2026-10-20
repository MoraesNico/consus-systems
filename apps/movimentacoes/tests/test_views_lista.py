"""Página Movimentações — livro-razão (FR-022–FR-026, FR-033; navegação da 001)."""

import re

import pytest

from apps.movimentacoes.services import registrar_movimentacao

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def test_fr022_fr033_colunas_e_formatos(client, produto_com_saldo):
    """FR-022/FR-033: data/hora, produto com link, selo do tipo, quantidade com sinal e saldo."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=5, observacao="NF 1")
    registrar_movimentacao(produto_id=produto.pk, tipo="SAIDA", quantidade=3)
    conteudo = html(client.get("/movimentacoes/"))
    assert re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", conteudo)
    assert f'href="/produtos/{produto.pk}/"' in conteudo and f"{produto.codigo}" in conteudo
    for trecho in ("Entrada", "Saída/Venda", "Saldo inicial", "+5", "−3", "10 → 15", "15 → 12",
                   "NF 1"):  # fmt: skip
        assert trecho in conteudo, trecho


def test_fr022_mais_recentes_primeiro(client, produto_com_saldo):
    """FR-022: ordem decrescente de registro."""
    produto = produto_com_saldo(saldo=10)
    registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=7)
    conteudo = html(client.get("/movimentacoes/"))
    assert conteudo.index("+7") < conteudo.index("Saldo inicial")


def test_fr023_fragmento_e_filtros(client, produto_com_saldo):
    """FR-023: HX-Target resultados devolve só o fragmento, filtrado."""
    a = produto_com_saldo(nome="Arruela")
    b = produto_com_saldo(nome="Bucha")
    registrar_movimentacao(produto_id=b.pk, tipo="ENTRADA", quantidade=2)
    resposta = client.get(f"/movimentacoes/?produto={a.pk}", HTTP_HX_REQUEST="true",
                          HTTP_HX_TARGET="resultados")  # fmt: skip
    conteudo = html(resposta)
    assert conteudo.lstrip().startswith('<div id="resultados"') and "<html" not in conteudo
    assert "Arruela" in conteudo and "Bucha" not in conteudo
    tipo = html(client.get(f"/movimentacoes/?tipo=ENTRADA&produto={b.pk}"))
    assert "+2" in tipo and "Saldo inicial" not in tipo.split('id="resultados"', 1)[1]


def test_fr024_paginacao_25_preservando_filtros(client, produto_com_saldo):
    """FR-024: 25 por página, links com ?pagina= preservando filtros, ajustes de página."""
    produto = produto_com_saldo(saldo=0)
    for _ in range(30):
        registrar_movimentacao(produto_id=produto.pk, tipo="ENTRADA", quantidade=1)
    pagina1 = html(client.get(f"/movimentacoes/?produto={produto.pk}"))
    assert pagina1.count('class="linha-movimentacao') == 25
    assert re.search(rf'href="\?produto={produto.pk}&amp;pagina=2"', pagina1)
    assert "page=" not in pagina1
    assert html(client.get("/movimentacoes/?pagina=99")).count('class="linha-movimentacao') == 6
    assert html(client.get("/movimentacoes/?pagina=x")).count('class="linha-movimentacao') == 25


def test_fr026_estados_vazios(client, produto_com_saldo):
    """FR-026: sem movimentações → registrar a primeira; com filtro sem resultado → limpar."""
    vazio = html(client.get("/movimentacoes/"))
    assert "Registre a primeira movimentação" in vazio
    produto = produto_com_saldo()
    filtrado = html(client.get(f"/movimentacoes/?produto={produto.pk}&tipo=SAIDA"))
    assert "Nenhuma movimentação encontrada." in filtrado and "Limpar filtros" in filtrado


def test_fr026_avisos_de_filtro_invalido(client):
    """FR-026: filtros inválidos aparecem como aviso (role=alert)."""
    conteudo = html(client.get("/movimentacoes/?de=2026-99-99&tipo=X"))
    assert 'role="alert"' in conteudo and "Data inicial inválida." in conteudo


def test_fr021_sem_acoes_de_edicao_na_lista(client, produto_com_saldo):
    """FR-021: o livro-razão não oferece editar nem excluir."""
    produto_com_saldo()
    conteudo = html(client.get("/movimentacoes/"))
    assert "Excluir" not in conteudo and "Editar" not in conteudo


def test_navegacao_movimentacoes_vira_link_e_fica_ativa(client):
    """001 FR-012/FR-013: o item Movimentações vira link e fica ativo nas páginas da 003."""
    for url in ("/movimentacoes/", "/movimentacoes/nova/"):
        nav = html(client.get(url)).split('aria-label="Principal"', 1)[1].split("</nav>", 1)[0]
        assert re.search(r'<a class="navegacao__item" href="/movimentacoes/" aria-current="page">',
                         nav)  # fmt: skip
    assert 'href="/movimentacoes/nova/"' in html(client.get("/movimentacoes/"))
