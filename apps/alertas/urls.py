from django.urls import path

from . import views

app_name = "alertas"

urlpatterns = [
    path("", views.relatorio, name="relatorio"),
    path("contador/", views.contador, name="contador"),
]
