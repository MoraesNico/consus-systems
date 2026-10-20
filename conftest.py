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
def _armazenamento_estatico_simples(settings):
    """O manifesto do WhiteNoise só existe após `collectstatic`; nos testes, storage simples."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
