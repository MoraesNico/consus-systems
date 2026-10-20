"""Integração real com Docker Compose (opt-in: `uv run pytest -m docker`).

FR-001, 002, 003, 007, 010, 035, 036, 041 e SC-005. Sobe um projeto isolado (`consus-teste`)
numa porta livre e derruba tudo (inclusive volumes) ao final.

Em ambientes que exigem build com CA própria, construa a imagem antes e defina
`CONSUS_DOCKER_SEM_BUILD=1` para reutilizá-la.
"""

import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(shutil.which("docker") is None, reason="docker indisponível"),
]

RAIZ = Path(__file__).resolve().parents[3]
PROJETO = "consus-teste"
ARQUIVO_ENV = RAIZ / ".env.teste-docker"


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def compose(*args: str, check: bool = True, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-p", PROJETO, "--env-file", str(ARQUIVO_ENV), *args],
        cwd=RAIZ,
        env={**os.environ, "CONSUS_ENV_FILE": str(ARQUIVO_ENV)},
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def obter(url: str, timeout: float = 5.0) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resposta:
            return resposta.status, resposta.read()
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read()


@pytest.fixture(scope="module")
def ambiente():
    porta = porta_livre()
    env = (RAIZ / ".env.example").read_text().replace("CONSUS_PORTA=8000", f"CONSUS_PORTA={porta}")
    ARQUIVO_ENV.write_text(env)
    args = ["up", "-d", "--wait", "--wait-timeout", "180"]
    if os.environ.get("CONSUS_DOCKER_SEM_BUILD") != "1":
        args.insert(1, "--build")
    try:
        compose(*args)
        yield f"http://127.0.0.1:{porta}"
    finally:
        compose("down", "-v", check=False)
        ARQUIVO_ENV.unlink(missing_ok=True)


def test_fr001_fr003_sobe_com_um_comando(ambiente):
    """FR-001/FR-003: `up` conclui com o banco subindo junto e o Painel responde 200."""
    limite = time.monotonic() + 120
    while time.monotonic() < limite:
        status, _ = obter(f"{ambiente}/")
        if status == 200:
            break
        time.sleep(2)
    assert status == 200


def test_fr002_migracoes_na_subida(ambiente):
    """FR-002: os logs do app mostram o migrate do entrypoint."""
    logs = compose("logs", "app").stdout
    assert "Apply" in logs or "No migrations to apply" in logs


def test_fr010_processo_nao_root(ambiente):
    """FR-010: o processo do app não roda como root."""
    assert compose("exec", "-T", "app", "id", "-u").stdout.strip() != "0"


def test_fr036_app_saudavel(ambiente):
    """FR-036: o healthcheck do app usa /saude/ e o serviço fica healthy."""
    assert "healthy" in compose("ps", "app").stdout


def test_fr035_sc005_saude_com_e_sem_banco(ambiente):
    """FR-035/SC-005: p95 < 1 s com banco; 503 em ≤ 3 s sem banco; volta a 200."""
    tempos = []
    for _ in range(20):
        inicio = time.monotonic()
        status, _ = obter(f"{ambiente}/saude/")
        tempos.append(time.monotonic() - inicio)
        assert status == 200
    tempos.sort()
    assert tempos[18] < 1.0
    compose("stop", "db")
    try:
        inicio = time.monotonic()
        status, _ = obter(f"{ambiente}/saude/", timeout=10)
        assert status == 503
        assert time.monotonic() - inicio <= 3.0
    finally:
        compose("start", "db")
    limite = time.monotonic() + 60
    while time.monotonic() < limite and obter(f"{ambiente}/saude/")[0] != 200:
        time.sleep(1)
    assert obter(f"{ambiente}/saude/")[0] == 200


def test_fr007_volume_persiste_apos_reinicio(ambiente):
    """FR-007: após restart do app, não há migrações pendentes (dados persistidos)."""
    compose("restart", "app")
    saida = compose("exec", "-T", "app", "python", "manage.py", "migrate", "--noinput").stdout
    assert "No migrations to apply" in saida


def test_fr041_suite_no_postgres(ambiente):
    """FR-041: o serviço de testes roda a suíte contra o PostgreSQL."""
    resultado = compose("--profile", "testes", "run", "--rm", "testes", check=False, timeout=900)
    assert resultado.returncode == 0, resultado.stdout[-4000:] + resultado.stderr[-2000:]
