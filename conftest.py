"""Configuração global da suíte de testes."""

import pytest


@pytest.fixture(autouse=True)
def _armazenamento_estatico_simples(settings):
    """O manifesto do WhiteNoise só existe após `collectstatic`; nos testes, storage simples."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
