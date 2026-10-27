"""010 — Execução só com Python: requirements em dia com o uv.lock e iniciar.py portátil."""

import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]


def _versoes_lock() -> dict[str, str]:
    dados = tomllib.loads((RAIZ / "uv.lock").read_text())
    return {p["name"].lower(): p["version"] for p in dados["package"] if "version" in p}


def test_fr001_requirements_batem_com_uv_lock():
    lock = _versoes_lock()
    for arquivo in ("requirements.txt", "requirements-dev.txt"):
        for linha in (RAIZ / arquivo).read_text().splitlines():
            casou = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)", linha)
            if casou:
                nome, versao = casou.group(1).lower(), casou.group(2)
                assert lock.get(nome) == versao, (arquivo, nome, versao, lock.get(nome))
    assert "django==" in (RAIZ / "requirements.txt").read_text()
    assert (RAIZ / "requirements-dev.txt").read_text().startswith("-r requirements.txt")


def test_fr002_python_311_e_ruff_py311():
    pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text())
    assert pyproject["project"]["requires-python"] == ">=3.11"
    assert pyproject["tool"]["ruff"]["target-version"] == "py311"
    assert "python:3.13" in (RAIZ / "Dockerfile").read_text()


def test_fr003_iniciar_usa_so_biblioteca_padrao():
    arvore = ast.parse((RAIZ / "iniciar.py").read_text())
    modulos = {
        (no.module or "").split(".")[0] if isinstance(no, ast.ImportFrom) else a.name.split(".")[0]
        for no in ast.walk(arvore)
        if isinstance(no, ast.Import | ast.ImportFrom)
        for a in (no.names if isinstance(no, ast.Import) else [no])
    }
    assert modulos - {"django"} <= set(sys.stdlib_module_names), modulos


def test_fr004_iniciar_ajuda_funciona():
    saida = subprocess.run([sys.executable, str(RAIZ / "iniciar.py"), "--help"],
                           capture_output=True, text=True, check=True).stdout  # fmt: skip
    for opcao in ("--porta", "--host", "--sem-demo"):
        assert opcao in saida


def test_fr005_readme_documenta_python_puro():
    readme = (RAIZ / "README.md").read_text()
    trechos = ("Rodar só com Python", "python iniciar.py", "Levar para outra máquina",
               "Usar PostgreSQL sem Docker", "Paleta de cores", "docker compose up")  # fmt: skip
    for trecho in trechos:
        assert trecho in readme, trecho
