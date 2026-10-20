"""Rotas do Consus. Cada feature acrescenta o seu `include` (docs/arquitetura.md)."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("produtos/", include("apps.produtos.urls")),
    path("movimentacoes/", include("apps.movimentacoes.urls")),
]
