from django.urls import path

from . import views

app_name = "financeiro"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("transacoes/", views.transacoes, name="transacoes"),
]
