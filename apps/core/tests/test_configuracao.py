"""Configuração por ambiente, localização e segurança (FR-004, 005, 006, 009, 020, 043, 044).

As leituras de settings rodam em subprocesso com ambiente controlado: as settings do Django são
carregadas uma única vez por processo, então só assim cada combinação de variáveis é testada.
"""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template
from django.utils import timezone

RAIZ = Path(__file__).resolve().parents[3]

SCRIPT_SETTINGS = """
import json, logging, sys
import django
django.setup()
from django.conf import settings
handler = settings.LOGGING["handlers"]["console"]
print(json.dumps({
    "DEBUG": settings.DEBUG,
    "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
    "CSRF_TRUSTED_ORIGINS": settings.CSRF_TRUSTED_ORIGINS,
    "ENGINE": settings.DATABASES["default"]["ENGINE"],
    "OPTIONS": settings.DATABASES["default"].get("OPTIONS", {}),
    "LOG_LEVEL": settings.LOGGING["root"]["level"],
    "LOG_STREAM": handler.get("stream"),
    "LOG_CLASS": handler["class"],
    "SESSION_COOKIE_SECURE": settings.SESSION_COOKIE_SECURE,
    "CSRF_COOKIE_SECURE": settings.CSRF_COOKIE_SECURE,
}))
"""

VARIAVEIS_LIMPAS = (
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "DATABASE_URL",
    "DATABASE_CONNECT_TIMEOUT",
    "DJANGO_LOG_LEVEL",
    "DJANGO_SECURE_COOKIES",
)


def carregar_settings(**variaveis: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in VARIAVEIS_LIMPAS}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"
    env.update(variaveis)
    return subprocess.run(
        [sys.executable, "-c", SCRIPT_SETTINGS],
        cwd=RAIZ,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def ler(**variaveis: str) -> dict:
    resultado = carregar_settings(**variaveis)
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout.strip().splitlines()[-1])


def test_fr004_le_variaveis_do_ambiente():
    """FR-004: hosts, origens CSRF, nível de log e timeout do banco vêm do ambiente."""
    lido = ler(
        DJANGO_SECRET_KEY="x",
        DJANGO_ALLOWED_HOSTS="consus.local, exemplo.com",
        DJANGO_CSRF_TRUSTED_ORIGINS="https://consus.local",
        DJANGO_LOG_LEVEL="WARNING",
        DATABASE_URL="postgres://u:s@db:5432/consus",
        DATABASE_CONNECT_TIMEOUT="7",
    )
    assert lido["ALLOWED_HOSTS"] == ["consus.local", "exemplo.com"]
    assert lido["CSRF_TRUSTED_ORIGINS"] == ["https://consus.local"]
    assert lido["LOG_LEVEL"] == "WARNING"
    assert lido["OPTIONS"]["connect_timeout"] == 7


def test_fr005_debug_desligado_por_padrao():
    """FR-005: DEBUG é falso quando DJANGO_DEBUG não é informado."""
    assert ler(DJANGO_SECRET_KEY="x")["DEBUG"] is False


def test_fr005_sem_chave_secreta_e_sem_debug_falha():
    """FR-005: sem DJANGO_SECRET_KEY com DEBUG falso o processo termina com erro explicativo."""
    resultado = carregar_settings(DJANGO_DEBUG="false")
    assert resultado.returncode != 0
    assert "DJANGO_SECRET_KEY" in resultado.stderr


def test_fr005_debug_aceita_valores_verdadeiros():
    """FR-005: DJANGO_DEBUG aceita 1/true/yes/on sem diferenciar maiúsculas."""
    for valor in ("1", "TRUE", "yes", "On"):
        assert ler(DJANGO_DEBUG=valor)["DEBUG"] is True


def test_fr006_sem_database_url_usa_sqlite():
    """FR-006: sem DATABASE_URL o banco é SQLite local."""
    assert ler(DJANGO_SECRET_KEY="x")["ENGINE"] == "django.db.backends.sqlite3"


def test_fr006_database_url_postgres_com_timeout_padrao():
    """FR-006: DATABASE_URL postgres:// seleciona PostgreSQL com connect_timeout padrão 2 s."""
    lido = ler(DJANGO_SECRET_KEY="x", DATABASE_URL="postgres://u:s@db:5432/consus")
    assert lido["ENGINE"] == "django.db.backends.postgresql"
    assert lido["OPTIONS"]["connect_timeout"] == 2


def test_fr009_logs_vao_para_stdout_no_nivel_configurado():
    """FR-009: um StreamHandler em stdout com o nível de DJANGO_LOG_LEVEL."""
    lido = ler(DJANGO_SECRET_KEY="x", DJANGO_LOG_LEVEL="ERROR")
    assert lido["LOG_CLASS"] == "logging.StreamHandler"
    assert lido["LOG_STREAM"] == "ext://sys.stdout"
    assert lido["LOG_LEVEL"] == "ERROR"


def test_fr020_localizacao_pt_br():
    """FR-020: pt-BR, fuso de São Paulo, milhar com ponto e datas dd/mm/aaaa HH:MM."""
    assert settings.LANGUAGE_CODE == "pt-br"
    assert settings.TIME_ZONE == "America/Sao_Paulo"
    assert settings.USE_THOUSAND_SEPARATOR is True
    assert Template("{{ valor }}").render(Context({"valor": 1240})) == "1.240"
    momento = timezone.make_aware(datetime.datetime(2026, 10, 20, 14, 30))
    renderizado = Template('{{ m|date:"SHORT_DATETIME_FORMAT" }}').render(Context({"m": momento}))
    assert renderizado == "20/10/2026 14:30"


def test_fr043_cabecalhos_de_seguranca(client):
    """FR-043: respostas trazem X-Frame-Options, nosniff e Referrer-Policy."""
    resposta = client.get("/nao-existe/")
    assert resposta["X-Frame-Options"] == "DENY"
    assert resposta["X-Content-Type-Options"] == "nosniff"
    assert resposta["Referrer-Policy"] == "same-origin"


def test_fr043_cookies_seguros_por_variavel():
    """FR-043: DJANGO_SECURE_COOKIES=true liga cookies de sessão e CSRF seguros."""
    assert ler(DJANGO_SECRET_KEY="x")["SESSION_COOKIE_SECURE"] is False
    lido = ler(DJANGO_SECRET_KEY="x", DJANGO_SECURE_COOKIES="true")
    assert lido["SESSION_COOKIE_SECURE"] is True
    assert lido["CSRF_COOKIE_SECURE"] is True


@pytest.mark.django_db
def test_fr044_admin_e_auth_nao_expostos(client):
    """FR-044: sem django.contrib.admin/auth e /admin/ responde 404."""
    assert "django.contrib.admin" not in settings.INSTALLED_APPS
    assert "django.contrib.auth" not in settings.INSTALLED_APPS
    assert client.get("/admin/").status_code == 404
