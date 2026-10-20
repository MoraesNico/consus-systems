"""Rotas do Consus. Cada feature acrescenta o seu `include` (docs/arquitetura.md)."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
]
