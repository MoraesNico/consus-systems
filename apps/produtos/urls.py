from django.urls import path

from . import views

app_name = "produtos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("previa-margem/", views.previa_margem, name="previa_margem"),
    path("<int:produto_id>/", views.detalhe, name="detalhe"),
    path("<int:produto_id>/editar/", views.editar, name="editar"),
]
