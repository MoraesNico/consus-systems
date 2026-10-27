from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
    path("senha/", views.trocar_senha, name="trocar_senha"),
]
