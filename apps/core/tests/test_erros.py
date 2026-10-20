"""Páginas de erro no estilo do Consus (FR-037, FR-038, FR-039, FR-018)."""

from pathlib import Path

import pytest
from django.db import connection
from django.template.loader import render_to_string
from django.test import Client
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db

RAIZ = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("htmx", [False, True])
def test_fr037_404_estilizada(client, htmx):
    """FR-037: 404 com navegação, código, caminho escapado em mono e link para o Painel."""
    extra = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    resposta = client.get("/nao-existe/<b>/", **extra)
    html = resposta.content.decode()
    assert resposta.status_code == 404
    assert 'aria-label="Principal"' in html
    assert "404" in html and "Voltar ao Painel" in html
    assert "/nao-existe/&lt;b&gt;/" in html and "pagina-erro__caminho" in html


def test_fr038_500_estilizada_sem_banco(urls_com_secoes):
    """FR-038: 500 sem traceback; o template renderiza sem request e sem consultas."""
    cliente = Client(raise_request_exception=False)
    resposta = cliente.get("/teste/erro-500/")
    html = resposta.content.decode()
    assert resposta.status_code == 500
    assert "500" in html and "Traceback" not in html and "falha de teste" not in html
    with CaptureQueriesContext(connection) as consultas:
        assert "Voltar ao Painel" in render_to_string("500.html")
    assert len(consultas) == 0


def test_fr039_403_400_e_csrf(urls_com_secoes):
    """FR-039: 403 com navegação, 403 de CSRF orientando recarregar, 400 estilizada."""
    cliente = Client(raise_request_exception=False)
    proibido = cliente.get("/teste/erro-403/")
    assert proibido.status_code == 403 and 'aria-label="Principal"' in proibido.content.decode()
    ruim = cliente.get("/teste/erro-400/")
    assert ruim.status_code == 400 and "Voltar ao Painel" in ruim.content.decode()
    csrf = Client(enforce_csrf_checks=True).post("/design/", {"exemplo": "toast"})
    assert csrf.status_code == 403
    assert "Recarregue a página" in csrf.content.decode()


def test_fr018_erros_parciais_viram_toast():
    """FR-018: consus.js mostra toast com o status em htmx:responseError."""
    js = (RAIZ / "static" / "js" / "consus.js").read_text()
    assert "htmx:responseError" in js and "Não foi possível concluir a ação (erro" in js
