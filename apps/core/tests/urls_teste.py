"""Urlconf de teste: rotas reais + namespaces fictícios das features 002–004 e views que falham."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import engines
from django.urls import include, path

PAGINA = engines["django"].from_string(
    '{% extends "base.html" %}{% block titulo %}Seção de teste{% endblock %}'
    "{% block conteudo %}<p>{{ request.path }}</p>{% endblock %}"
)

NIVEIS = {
    "sucesso": messages.SUCCESS,
    "info": messages.INFO,
    "alerta": messages.WARNING,
    "erro": messages.ERROR,
}


def pagina_simples(request, **kwargs):
    return HttpResponse(PAGINA.render({}, request))


def mensagem(request, nivel):
    messages.add_message(request, NIVEIS[nivel], f"Mensagem de {nivel}.")
    return redirect("core:painel")


def erro_500(request):
    raise RuntimeError("falha de teste")


def erro_400(request):
    raise SuspiciousOperation("requisição suspeita")


def erro_403(request):
    raise PermissionDenied


produtos = (
    [
        path("", pagina_simples, name="lista"),
        path("novo/", pagina_simples, name="novo"),
        path("<int:pk>/", pagina_simples, name="detalhe"),
    ],
    "produtos",
)
movimentacoes = ([path("", pagina_simples, name="lista")], "movimentacoes")
financeiro = (
    [
        path("", pagina_simples, name="painel"),
        path("transacoes/", pagina_simples, name="transacoes"),
    ],
    "financeiro",
)
alertas = (
    [
        path("", pagina_simples, name="relatorio"),
        path("contador/", pagina_simples, name="contador"),
    ],
    "alertas",
)

urlpatterns = [
    path("", include("apps.core.urls")),
    path("produtos/", include(produtos)),
    path("movimentacoes/", include(movimentacoes)),
    path("financeiro/", include(financeiro)),
    path("alertas/", include(alertas)),
    path("contas/", include("apps.contas.urls")),
    path("teste/mensagem/<str:nivel>/", mensagem),
    path("teste/erro-500/", erro_500),
    path("teste/erro-400/", erro_400),
    path("teste/erro-403/", erro_403),
]
