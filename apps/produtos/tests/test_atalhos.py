"""Atalhos de teclado progressivos (FR-028)."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.django_db

RAIZ = Path(__file__).resolve().parents[3]


def test_fr028_busca_tem_data_atalho_barra_e_dica(client):
    """FR-028: "/" foca a busca, com dica <kbd>/</kbd>."""
    conteudo = client.get("/produtos/").content.decode()
    assert re.search(r'<input[^>]+name="q"[^>]+data-atalho="/"', conteudo)
    assert "<kbd>/</kbd>" in conteudo


def test_fr028_novo_produto_tem_data_atalho_n_e_href_funcional(client):
    """FR-028: "n" abre o cadastro; o link funciona sem JS."""
    conteudo = client.get("/produtos/").content.decode()
    acao = re.search(r'<a[^>]+data-atalho="n"[^>]*>', conteudo).group(0)
    assert 'href="/produtos/novo/"' in acao
    assert "<kbd>n</kbd>" in conteudo


def test_fr028_script_progressivo_carregado(client):
    """FR-028: a página carrega o consus.js que trata data-atalho."""
    assert "js/consus.js" in client.get("/produtos/").content.decode()
    assert "data-atalho" in (RAIZ / "static" / "js" / "consus.js").read_text()


def test_fr028_js_proprio_abaixo_de_100_linhas():
    """Constituição II: JS próprio (fora de vendor/) com menos de 100 linhas."""
    total = sum(len(f.read_text().splitlines()) for f in (RAIZ / "static" / "js").glob("*.js"))
    assert total < 100
