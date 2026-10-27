"""Urlconf apenas com o core: simula o sistema antes das features 002–004."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("contas/", include("apps.contas.urls")),
]
