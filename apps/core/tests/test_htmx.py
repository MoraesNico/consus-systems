"""Utilitários HTMX do core (FR-015, FR-017, FR-018)."""

import json

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django_htmx.middleware import HtmxDetails

from apps.core.htmx import disparar_evento, disparar_toast, eh_fragmento

fabrica = RequestFactory()


def requisicao(**cabecalhos):
    request = fabrica.get("/", **cabecalhos)
    request.htmx = HtmxDetails(request)
    return request


def gatilhos(resposta) -> dict:
    return json.loads(resposta["HX-Trigger"])


def test_fr018_eh_fragmento():
    """FR-018: fragmento só para HTMX que não seja boost nem restauração de histórico."""
    assert eh_fragmento(requisicao()) is False
    assert eh_fragmento(requisicao(HTTP_HX_REQUEST="true", HTTP_HX_BOOSTED="true")) is False
    assert (
        eh_fragmento(requisicao(HTTP_HX_REQUEST="true", HTTP_HX_HISTORY_RESTORE_REQUEST="true"))
        is False
    )
    assert eh_fragmento(requisicao(HTTP_HX_REQUEST="true")) is True


def test_fr015_disparar_toast_padrao_sucesso():
    """FR-015: disparar_toast grava o evento toast com nível e texto."""
    resposta = disparar_toast(HttpResponse(), "sucesso", "Salvo.")
    assert gatilhos(resposta) == {"toast": {"nivel": "sucesso", "texto": "Salvo."}}


@pytest.mark.parametrize("nivel", ["sucesso", "info", "alerta", "erro"])
def test_fr015_niveis_validos(nivel):
    """FR-015: os quatro níveis do contrato são aceitos."""
    assert gatilhos(disparar_toast(HttpResponse(), nivel, "Ok."))["toast"]["nivel"] == nivel


@pytest.mark.parametrize(
    ("texto", "nivel"),
    [("Ok.", "perigo"), ("", "info"), ("x" * 201, "info")],
)
def test_fr015_toast_invalido_levanta_erro(texto, nivel):
    """FR-015: nível fora do vocabulário ou texto vazio/longo demais ⇒ ValueError."""
    with pytest.raises(ValueError):
        disparar_toast(HttpResponse(), nivel, texto)


def test_fr017_eventos_se_mesclam_no_mesmo_cabecalho():
    """FR-017: fechar-dialogo, toast e estoque-alterado convivem no mesmo HX-Trigger."""
    resposta = disparar_evento(HttpResponse(), "estoque-alterado", {"produto_id": 1})
    disparar_evento(resposta, "fechar-dialogo")
    disparar_toast(resposta, "sucesso", "Entrada registrada.")
    assert gatilhos(resposta) == {
        "estoque-alterado": {"produto_id": 1},
        "fechar-dialogo": {},
        "toast": {"nivel": "sucesso", "texto": "Entrada registrada."},
    }
