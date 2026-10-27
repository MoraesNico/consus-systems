"""Clientes de teste já autenticados (006: login obrigatório em todas as páginas)."""

from django.contrib.auth import get_user_model
from django.test import Client as ClienteDjango


def Client(**kwargs) -> ClienteDjango:  # noqa: N802 - substitui django.test.Client nos testes
    cliente = ClienteDjango(**kwargs)
    usuario, _ = get_user_model().objects.get_or_create(username="operador")
    cliente.force_login(usuario)
    return cliente
