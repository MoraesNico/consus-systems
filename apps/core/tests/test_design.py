"""Catálogo vivo do design system em /design/ (FR-031, FR-032, FR-033)."""

import json

import pytest
from django.test import Client

from apps.core import design_tokens
from apps.core.views import COMPONENTES_CATALOGO

pytestmark = pytest.mark.django_db

ANCORAS_TOKENS = ["cores", "contraste", "tipografia", "espacamento", "tamanhos", "bordas",
                  "sombras", "camadas", "movimento"]  # fmt: skip


@pytest.mark.parametrize("variante", ["normal", "boost", "htmx"])
def test_fr031_catalogo_completo(client, variante):
    """FR-031: sumário com 9 seções de tokens e 18 componentes, contraste calculado, trechos."""
    if variante != "normal":
        client.defaults["HTTP_HX_REQUEST"] = "true"
    if variante == "boost":
        client.defaults["HTTP_HX_BOOSTED"] = "true"
    resposta = client.get("/design/")
    html = resposta.content.decode()
    assert resposta.status_code == 200
    assert len(COMPONENTES_CATALOGO) == 18
    for ancora in ANCORAS_TOKENS + [a for a, _, _ in COMPONENTES_CATALOGO]:
        assert f'href="#{ancora}"' in html, ancora
        assert f'id="{ancora}"' in html, ancora
    for par in design_tokens.avaliar_pares():
        assert f"{par['razao']:.2f}".replace(".", ",") + ":1" in html
    for ancora, _, _ in COMPONENTES_CATALOGO:
        secao = html.split(f'id="{ancora}"', 1)[1].split("</section>", 1)[0]
        assert "<pre" in secao and "<code>" in secao, ancora


def test_fr032_dialogo_de_exemplo(client, cliente_htmx):
    """FR-032: ?exemplo=dialogo devolve fragmento com HTMX e página sem HTMX."""
    fragmento = cliente_htmx.get("/design/?exemplo=dialogo").content.decode()
    assert 'id="dialogo-titulo"' in fragmento and "autofocus" in fragmento
    assert "data-toasts" in fragmento and "<html" not in fragmento
    pagina = Client().get("/design/?exemplo=dialogo").content.decode()
    assert "<html" in pagina and 'id="dialogo-titulo"' in pagina and "Voltar" in pagina


@pytest.mark.parametrize("nivel", ["sucesso", "info", "alerta", "erro"])
def test_fr032_toasts_de_exemplo(client, cliente_htmx, nivel):
    """FR-032: POST toast → 204 + HX-Trigger (HTMX) ou 302 + mensagem (sem HTMX)."""
    resposta = cliente_htmx.post("/design/", {"exemplo": "toast", "nivel": nivel})
    assert resposta.status_code == 204
    assert json.loads(resposta["HX-Trigger"])["toast"]["nivel"] == nivel
    normal = Client().post("/design/", {"exemplo": "toast", "nivel": nivel})
    assert normal.status_code == 302 and normal["Location"] == "/design/#toast"


def test_fr032_formulario_422_e_sucesso(cliente_htmx):
    """FR-032: inválido → 422 com aria-invalid; válido → 200 com fechar-dialogo e toast."""
    invalido = cliente_htmx.post(
        "/design/", {"exemplo": "formulario", "nome": "", "quantidade": ""}
    )
    assert invalido.status_code == 422
    assert 'aria-invalid="true"' in invalido.content.decode()
    valido = cliente_htmx.post("/design/", {"exemplo": "formulario", "nome": "Caneta",
                                            "quantidade": "3"})  # fmt: skip
    gatilhos = json.loads(valido["HX-Trigger"])
    assert valido.status_code == 200
    assert "fechar-dialogo" in gatilhos and gatilhos["toast"]["nivel"] == "sucesso"


def test_fr032_formulario_sem_htmx():
    """FR-032: sem HTMX, inválido → página 422; válido → 302 com mensagem."""
    cliente = Client()
    invalido = cliente.post("/design/", {"exemplo": "formulario", "nome": "", "quantidade": "0"})
    assert invalido.status_code == 422 and "<html" in invalido.content.decode()
    valido = cliente.post("/design/", {"exemplo": "formulario", "nome": "X", "quantidade": "2"})
    assert valido.status_code == 302 and valido["Location"] == "/design/#dialogo"


@pytest.mark.parametrize(
    "dados", [{"exemplo": "outro"}, {"exemplo": "toast", "nivel": "perigo"}, {}]
)
def test_fr032_valores_invalidos_400(client, dados):
    """FR-032: exemplo ou nível desconhecido → 400."""
    assert client.post("/design/", dados).status_code == 400


def test_fr032_get_exemplo_invalido_400(client):
    """FR-032: ?exemplo desconhecido → 400."""
    assert client.get("/design/?exemplo=foguete").status_code == 400


def test_fr033_catalogo_disponivel_sem_debug_e_fora_da_navegacao(client, settings):
    """FR-033: funciona com DEBUG falso, noindex, fora da navegação e com dados "Exemplo"."""
    settings.DEBUG = False
    html = client.get("/design/").content.decode()
    assert '<meta name="robots" content="noindex, nofollow">' in html
    navegacao = html.split('aria-label="Principal"', 1)[1].split("</nav>", 1)[0]
    assert "/design/" not in navegacao
    assert "Exemplo" in html or "exemplo" in html
