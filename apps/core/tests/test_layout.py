"""Casca da aplicação: base.html, toasts, diálogo e configuração HTMX (FR-011, 015–021, 023)."""

import json
import re
from pathlib import Path

import pytest
from django.middleware.csrf import _unmask_cipher_token

pytestmark = pytest.mark.django_db

RAIZ = Path(__file__).resolve().parents[3]
CONSUS_JS = RAIZ / "static" / "js" / "consus.js"


def html(resposta) -> str:
    return resposta.content.decode()


@pytest.fixture(params=["normal", "htmx", "boost"])
def resposta_painel(request, client, db):
    if request.param in ("htmx", "boost"):
        client.defaults["HTTP_HX_REQUEST"] = "true"
    if request.param == "boost":
        client.defaults["HTTP_HX_BOOSTED"] = "true"
    # /design/ devolve a página completa nas três variantes (o Painel ganhou fragmento na 004).
    return client.get("/design/")


def test_fr011_estrutura_da_casca(resposta_painel):
    """FR-011: link de pular é o 1º focável; marca liga ao Painel; main#conteudo; rodapé."""
    conteudo = html(resposta_painel)
    corpo = conteudo.split("<body", 1)[1]
    primeiro_focavel = re.search(r"<(a|button|input|select|textarea)\b[^>]*>", corpo).group(0)
    assert 'class="pular-conteudo"' in primeiro_focavel
    assert 'href="#conteudo"' in primeiro_focavel
    assert re.search(
        r'<a[^>]+class="marca"[^>]+href="/"|<a[^>]+href="/"[^>]+class="marca"', conteudo
    )
    assert "Consus" in conteudo
    assert '<main id="conteudo"' in conteudo
    rodape = conteudo.split('class="rodape-app"', 1)[1]
    assert "v1.0.0" in rodape
    assert 'href="/design/"' in rodape
    assert 'href="/saude/"' in rodape


def test_fr015_regiao_de_toasts(resposta_painel):
    """FR-015: região de toasts status/polite preservada entre navegações + modelo de toast."""
    conteudo = html(resposta_painel)
    regiao = re.search(r'<div id="toasts"[^>]*>', conteudo).group(0)
    assert 'role="status"' in regiao
    assert 'aria-live="polite"' in regiao
    assert "hx-preserve" in regiao
    assert '<template id="modelo-toast">' in conteudo


@pytest.mark.parametrize("nivel", ["sucesso", "info", "alerta", "erro"])
def test_fr015_mensagens_do_servidor_viram_aviso(client, urls_com_secoes, nivel):
    """FR-015: mensagens do Django aparecem em [data-mensagens] no nível mapeado."""
    resposta = client.get(f"/teste/mensagem/{nivel}/", follow=True)
    conteudo = html(resposta)
    bloco = conteudo.split("data-mensagens", 1)[1].split("</div>\n", 1)[0]
    assert f"aviso--{nivel}" in bloco
    assert f"Mensagem de {nivel}." in bloco


def test_fr016_duracao_e_maximo_de_toasts(resposta_painel):
    """FR-016: duração de 5 s e no máximo 3 toasts; alerta/erro com role=alert no cliente."""
    regiao = re.search(r'<div id="toasts"[^>]*>', html(resposta_painel)).group(0)
    assert 'data-duracao-ms="5000"' in regiao
    assert 'data-maximo="3"' in regiao
    js = CONSUS_JS.read_text()
    assert "duracaoMs" in js or "data-duracao-ms" in js or "duracao" in js
    assert '"alert"' in js


def test_fr017_dialogo_unico(resposta_painel):
    """FR-017: <dialog id="dialogo"> único rotulado por #dialogo-titulo; JS trata o ciclo."""
    conteudo = html(resposta_painel)
    assert conteudo.count("<dialog") == 1
    assert re.search(r'<dialog id="dialogo"[^>]*aria-labelledby="dialogo-titulo"', conteudo)
    js = CONSUS_JS.read_text()
    for trecho in ("showModal", "close", "fechar-dialogo", "data-toasts"):
        assert trecho in js, trecho


def test_fr018_htmx_boost_csrf_e_configuracao(client):
    """FR-018: hx-boost, CSRF em hx-headers, htmx-config (204/422/4xx) e HTMX local."""
    resposta = client.get("/")
    conteudo = html(resposta)
    corpo = re.search(r"<body[^>]*>", conteudo).group(0)
    assert 'hx-boost="true"' in corpo
    cabecalhos = json.loads(re.search(r"hx-headers='([^']+)'", corpo).group(1))
    token = cabecalhos["X-CSRFToken"]
    cookie = resposta.cookies["csrftoken"].value
    assert _unmask_cipher_token(token) == cookie
    meta = re.search(r'<meta name="htmx-config" content=\'([^\']+)\'', conteudo).group(1)
    config = json.loads(meta)
    regras = {regra["code"]: regra for regra in config["responseHandling"]}
    assert regras["204"]["swap"] is False
    assert regras["422"]["swap"] is True
    assert regras["[45].."]["swap"] is False and regras["[45].."]["error"] is True
    assert config["historyCacheSize"] == 0
    assert re.search(r'<script[^>]+src="/static/vendor/htmx\.min\.js"', conteudo)
    js = CONSUS_JS.read_text()
    assert "htmx:responseError" in js and "htmx:sendError" in js


def test_fr019_titulo_da_pagina(client):
    """FR-019: <title> no formato "<Título> — Consus"."""
    assert "<title>Painel — Consus</title>" in html(client.get("/"))


def test_fr020_idioma_do_documento(client):
    """FR-020: <html lang="pt-BR">."""
    assert '<html lang="pt-BR">' in html(client.get("/"))


def test_fr021_responsivo(client):
    """FR-021: viewport; navegação rola na horizontal; tabela rola no contêiner."""
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html(
        client.get("/")
    )
    base = (RAIZ / "static" / "css" / "base.css").read_text()
    lista = re.search(r"\.navegacao__lista\s*\{[^}]*\}", base).group(0)
    assert "overflow-x: auto" in lista
    componentes = (RAIZ / "static" / "css" / "components.css").read_text()
    contenedor = re.search(r"\.tabela-contenedor\s*\{[^}]*\}", componentes).group(0)
    assert "overflow-x: auto" in contenedor


def test_fr023_tema_claro(client):
    """FR-023: só tema claro (color-scheme light)."""
    assert '<meta name="color-scheme" content="light">' in html(client.get("/"))


def test_constituicao_ii_js_proprio_pequeno():
    """Constituição 1.1.0: JavaScript próprio com menos de 200 linhas."""
    linhas = CONSUS_JS.read_text().splitlines()
    assert len(linhas) < 200, len(linhas)


def test_fr045_atalhos_declarativos():
    """FR-045: data-atalho genérico que ignora campos editáveis, modificadores e diálogo aberto."""
    js = CONSUS_JS.read_text()
    for trecho in ("data-atalho", "ctrlKey", "metaKey", "altKey", "contenteditable", ".open"):
        assert trecho in js, trecho
