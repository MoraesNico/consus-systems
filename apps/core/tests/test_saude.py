"""Verificação de saúde /saude/ (FR-034, FR-035)."""

import pytest
from django.db import OperationalError, connections
from django.test import Client

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("htmx", [False, True])
def test_fr034_contrato_json(htmx):
    """FR-034: GET 200 JSON com status/banco/versao, sem cache, sem cookie e sem CSRF."""
    cliente = Client(enforce_csrf_checks=True)
    extra = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    resposta = cliente.get("/saude/", **extra)
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "application/json"
    assert resposta.json() == {"status": "ok", "banco": "ok", "versao": "0.1.0"}
    assert "no-store" in resposta["Cache-Control"]
    assert not resposta.cookies


def test_fr034_head_e_metodos_nao_permitidos(client):
    """FR-034: HEAD sem corpo; POST/PUT/DELETE → 405 com Allow: GET, HEAD."""
    cabeca = client.head("/saude/")
    assert cabeca.status_code == 200 and cabeca.content == b""
    for metodo in ("post", "put", "delete"):
        resposta = getattr(client, metodo)("/saude/")
        assert resposta.status_code == 405
        assert "GET" in resposta["Allow"] and "HEAD" in resposta["Allow"]


def test_fr035_banco_indisponivel_503_sem_vazar_detalhes(client, monkeypatch):
    """FR-035: falha de conexão → 503 sem texto da exceção."""

    def falhar(alias):
        raise OperationalError("senha=segredo host=db")

    monkeypatch.setattr(connections, "create_connection", falhar)
    resposta = client.get("/saude/")
    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel", "versao": "0.1.0"}
    assert b"segredo" not in resposta.content


def test_fr035_conexao_criada_e_sempre_fechada(client, monkeypatch):
    """FR-035: a conexão nova é fechada mesmo quando a consulta falha."""
    fechadas = []
    original = connections.create_connection

    def criar(alias):
        conexao = original(alias)
        fechar = conexao.close

        def fechar_registrando():
            fechadas.append(True)
            fechar()

        conexao.close = fechar_registrando
        conexao.cursor = lambda: (_ for _ in ()).throw(OperationalError("caiu"))
        return conexao

    monkeypatch.setattr(connections, "create_connection", criar)
    assert client.get("/saude/").status_code == 503
    assert fechadas == [True]
