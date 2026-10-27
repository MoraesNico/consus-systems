"""Painel com KPIs da feature 004 (FR-022–FR-025, FR-036 da 004)."""

import re

import pytest

from apps.produtos.tests import PRECOS_TESTE

pytestmark = pytest.mark.django_db


def html(resposta) -> str:
    return resposta.content.decode()


def texto(conteudo: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", conteudo))


@pytest.fixture
def estoque(db):
    from apps.movimentacoes.services import registrar_movimentacao
    from apps.produtos.services import cadastrar_produto

    produtos = [
        cadastrar_produto(
            **PRECOS_TESTE, nome=f"Item {i:02d}", quantidade_inicial=100, estoque_minimo=10
        )
        for i in range(10)
    ]
    cadastrar_produto(**PRECOS_TESTE, nome="Zerado", quantidade_inicial=0, estoque_minimo=5)
    cadastrar_produto(**PRECOS_TESTE, nome="Baixo", quantidade_inicial=250, estoque_minimo=300)
    for _ in range(3):
        registrar_movimentacao(produto_id=produtos[0].pk, tipo="SAIDA", quantidade=1)
    return produtos


def test_fr022_kpis(client, estoque):
    """FR-022/FR-036: produtos, unidades (milhar), alertas e movimentações de 24 h."""
    resposta = client.get("/")
    painel = texto(html(resposta).split('id="painel-kpis"', 1)[1])
    assert resposta.status_code == 200 and "core/painel.html" in [
        t.name for t in resposta.templates
    ]
    assert "PRODUTOS CADASTRADOS 12" in painel.upper()
    assert "1.247" in painel
    assert re.search(r"EM ALERTA 2 .*1 sem estoque", painel, re.I)
    assert "Reposição necessária" in painel and "Cobertura do mínimo" in painel
    assert "Últimas movimentações" in painel


def test_fr023_criticos_com_entrada_e_link_para_relatorio(client, criar_produtos_em_alerta):
    """FR-023: até 5 críticos, "+ Entrada" com origem=alertas e link para o relatório."""
    conteudo = html(client.get("/")).split('id="painel-kpis"', 1)[1]
    assert conteudo.count('class="linha-critica') == 5
    assert "Ver relatório completo (7)" in texto(conteudo)
    assert "origem=alertas" in conteudo


@pytest.fixture
def criar_produtos_em_alerta(db):
    from apps.produtos.services import cadastrar_produto

    for i in range(7):
        cadastrar_produto(
            **PRECOS_TESTE, nome=f"Crítico {i}", quantidade_inicial=i, estoque_minimo=10
        )


def test_fr022_painel_vazio(client, db):
    """FR-022: sem produtos → KPIs zerados e convite a cadastrar."""
    conteudo = html(client.get("/")).split('id="painel-kpis"', 1)[1]
    assert "Cadastre o primeiro produto" in conteudo and 'href="/produtos/novo/"' in conteudo


def test_fr023_fr025_estados_vazios(client, db):
    """FR-023/FR-024/FR-025: sem alertas, sem mínimo e sem movimentações de E/S."""
    from apps.produtos.services import cadastrar_produto

    cadastrar_produto(**PRECOS_TESTE, nome="Sem mínimo", quantidade_inicial=5, estoque_minimo=0)
    conteudo = texto(html(client.get("/")).split('id="painel-kpis"', 1)[1])
    assert "Nenhum produto precisa de reposição." in conteudo
    assert "Sem produtos com estoque mínimo definido." in conteudo


def test_fr022_fragmento_htmx_e_auto_atualizacao(client, estoque):
    """FR-022/FR-026 (004): só #painel-kpis via HTMX, recarregado sozinho em estoque-alterado."""
    conteudo = html(client.get("/", HTTP_HX_REQUEST="true"))
    assert "<html" not in conteudo
    raiz = re.search(r'<section id="painel-kpis"[^>]*>', conteudo).group(0)
    assert 'hx-trigger="estoque-alterado from:body"' in raiz and 'hx-get="/"' in raiz
    assert 'hx-swap="outerHTML"' in raiz


def test_painel_consultas_limitadas(client, estoque, django_assert_max_num_queries):
    """SC-005: no máximo 7 consultas na página completa do painel."""
    with django_assert_max_num_queries(9):  # 7 da 004 + 2 da faixa financeira (009)
        client.get("/")
