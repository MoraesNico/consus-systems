"""Configuração global da suíte de testes."""

import pytest
from django.db import connection


def pytest_collection_modifyitems(config, items):
    """Testes marcados `postgres` só rodam no PostgreSQL (contrato v1.1)."""
    if connection.vendor == "postgresql":
        return
    pular = pytest.mark.skip(reason="requer PostgreSQL")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(pular)


@pytest.fixture(autouse=True)
def _hash_de_senha_rapido(settings):
    """PBKDF2 real deixa a suíte lenta; nos testes basta um hasher barato."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def _armazenamento_estatico_simples(settings):
    """O manifesto do WhiteNoise só existe após `collectstatic`; nos testes, storage simples."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def usuario(django_user_model):
    """Usuário padrão dos testes (006: login obrigatório em todas as páginas)."""
    return django_user_model.objects.create_user(username="operador", password="senha-forte-123")


@pytest.fixture
def client(client, request):
    """`client` autenticado por padrão; use `cliente_anonimo` para cenários sem login."""
    if "django_db" in request.keywords or "db" in request.fixturenames:
        usuario = request.getfixturevalue("usuario")
        client.force_login(usuario)
    return client


@pytest.fixture
def cliente_anonimo():
    from django.test import Client

    return Client()
