"""Verificação textual dos arquivos de contêiner (FR-001–004, 007, 010, 036)."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
COMPOSE = (RAIZ / "docker-compose.yml").read_text()
DOCKERFILE = (RAIZ / "Dockerfile").read_text()
ENTRYPOINT = (RAIZ / "entrypoint.sh").read_text()
ENV_EXEMPLO = (RAIZ / ".env.example").read_text()

VARIAVEIS = [
    "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS", "DJANGO_CSRF_TRUSTED_ORIGINS",
    "DATABASE_URL", "DATABASE_CONNECT_TIMEOUT", "DJANGO_LOG_LEVEL", "DJANGO_SECURE_COOKIES",
    "WEB_CONCURRENCY", "CONSUS_PORTA", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
]


def servico(nome: str) -> str:
    """Bloco YAML de um serviço (até o próximo serviço de mesma indentação)."""
    return re.search(rf"\n  {nome}:\n(.*?)(?=\n  \w[\w-]*:\n|\nvolumes:|\Z)", COMPOSE, re.S).group(1)


def estagio(nome: str) -> str:
    return re.search(rf"FROM [^\n]+ AS {nome}\n(.*?)(?=\nFROM |\Z)", DOCKERFILE, re.S).group(1)


def test_fr001_servicos_db_e_app():
    """FR-001: compose com db e app; app construído no estágio producao, com .env e porta."""
    app = servico("app")
    assert "db:" in COMPOSE
    assert "target: producao" in app
    assert ".env" in app
    assert '"${CONSUS_PORTA:-8000}:8000"' in app


def test_fr002_estaticos_no_build_e_migracoes_na_subida():
    """FR-002: collectstatic no estágio producao; entrypoint migra com retry e só então executa."""
    assert "collectstatic --noinput" in estagio("producao")
    assert "set -eu" in ENTRYPOINT
    assert "migrate --noinput" in ENTRYPOINT
    assert re.search(r"\b15\b", ENTRYPOINT)
    assert "exit 1" in ENTRYPOINT
    assert ENTRYPOINT.rstrip().endswith('exec "$@"')


def test_fr003_app_espera_banco_saudavel():
    """FR-003: app depende do db saudável; db tem healthcheck pg_isready."""
    app = servico("app")
    assert re.search(r"depends_on:\s*\n\s+db:\s*\n\s+condition: service_healthy", app)
    assert "pg_isready" in servico("db")


def test_fr004_env_exemplo_documentado():
    """FR-004: cada variável do data-model §1 aparece precedida de comentário."""
    linhas = ENV_EXEMPLO.splitlines()
    for variavel in VARIAVEIS:
        indice = next(i for i, linha in enumerate(linhas) if linha.startswith(f"{variavel}="))
        assert linhas[indice - 1].startswith("#"), variavel
    assert "DJANGO_SECRET_KEY=troque-" in ENV_EXEMPLO


def test_fr007_volume_persistente_do_banco():
    """FR-007: volume nomeado dados_postgres montado no diretório de dados do PostgreSQL."""
    assert "dados_postgres:/var/lib/postgresql/data" in servico("db")
    assert re.search(r"\nvolumes:\s*\n\s+dados_postgres:", COMPOSE)


def test_fr010_processo_sem_root():
    """FR-010: o estágio producao termina com USER não-root."""
    usuarios = re.findall(r"^USER (\S+)", estagio("producao"), re.M)
    assert usuarios and usuarios[-1] not in ("root", "0")


def test_fr036_healthchecks():
    """FR-036: app consulta /saude/ com timeout; db tem healthcheck e app depende dele."""
    app = servico("app")
    assert "http://127.0.0.1:8000/saude/" in app
    assert "timeout=" in app
    assert "healthcheck:" in servico("db")
