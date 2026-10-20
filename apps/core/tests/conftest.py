"""Fixtures do app core: clientes HTMX e urlconf com seções fictícias das features 002–004."""

import pytest


@pytest.fixture
def cliente_htmx(client):
    """Requisição parcial: HX-Request sem HX-Boosted."""
    client.defaults["HTTP_HX_REQUEST"] = "true"
    return client


@pytest.fixture
def cliente_boost(client):
    """Navegação boostada: HX-Request + HX-Boosted (recebe a página completa)."""
    client.defaults["HTTP_HX_REQUEST"] = "true"
    client.defaults["HTTP_HX_BOOSTED"] = "true"
    return client


@pytest.fixture
def urls_com_secoes(settings):
    """Simula as features 002–004 registrando suas rotas (navegação deixa de ser "em breve")."""
    settings.ROOT_URLCONF = "apps.core.tests.urls_teste"
    from django.urls import clear_url_caches

    clear_url_caches()
    yield
    clear_url_caches()


@pytest.fixture
def urls_sem_secoes(settings):
    """Somente o core: Produtos, Movimentações e Alertas ficam "(em breve)"."""
    settings.ROOT_URLCONF = "apps.core.tests.urls_core"
    from django.urls import clear_url_caches

    clear_url_caches()
    yield
    clear_url_caches()
