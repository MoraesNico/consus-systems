from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("design/", views.design, name="design"),
    path("saude/", views.saude, name="saude"),
]
