from django.urls import path

from . import views

app_name = "produtos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("<int:produto_id>/", views.detalhe, name="detalhe"),
    path("<int:produto_id>/editar/", views.editar, name="editar"),
]
