"""Quality gates do projeto (FR-040, FR-041, FR-042)."""

import shutil
import subprocess
import tomllib
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

RAIZ = Path(__file__).resolve().parents[3]


def rodar(*comando: str) -> subprocess.CompletedProcess:
    return subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, timeout=300)


@pytest.mark.skipif(shutil.which("ruff") is None and shutil.which("uv") is None,
                    reason="ruff indisponível")  # fmt: skip
def test_fr040_ruff_lint_e_formatacao():
    """FR-040: `ruff check` e `ruff format --check` terminam sem erro."""
    ruff = shutil.which("ruff")
    base = [ruff] if ruff else ["uv", "run", "ruff"]
    assert rodar(*base, "check", ".").returncode == 0
    assert rodar(*base, "format", "--check", ".").returncode == 0


def test_fr041_cobertura_e_servico_de_testes():
    """FR-041: cobertura mínima de 90 % e serviço de testes no PostgreSQL via Compose."""
    config = tomllib.loads((RAIZ / "pyproject.toml").read_text())
    assert config["tool"]["coverage"]["report"]["fail_under"] >= 90
    assert {"apps", "config"} <= set(config["tool"]["coverage"]["run"]["source"])
    compose = (RAIZ / "docker-compose.yml").read_text()
    testes = compose.split("\n  testes:\n", 1)[1]
    assert 'profiles: ["testes"]' in testes and "target: testes" in testes
    assert "@db:5432" in testes


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv indisponível")
def test_fr042_lock_atualizado():
    """FR-042: uv.lock existe e está sincronizado com o pyproject."""
    assert (RAIZ / "uv.lock").is_file()
    assert rodar("uv", "lock", "--check").returncode == 0


@pytest.mark.django_db
def test_fr042_sem_migracoes_pendentes():
    """FR-042: `makemigrations --check` não encontra mudanças de modelo sem migração."""
    call_command("makemigrations", "--check", "--dry-run", stdout=StringIO())
