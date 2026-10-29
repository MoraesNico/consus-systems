#!/usr/bin/env python3
"""Inicia o Consus só com Python (sem Docker) — Windows, macOS e Linux.

Uso:
    python iniciar.py                 # migra, popula a demonstração na 1ª vez e abre o servidor
    python iniciar.py --sem-demo      # não cria os produtos de demonstração
    python iniciar.py --porta 8080 --host 0.0.0.0

Só usa a biblioteca padrão. Instale antes as dependências: `pip install -r requirements.txt`.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MARCA_DEMO = RAIZ / ".consus-demo-criada"
VERSAO_MINIMA = (3, 11)
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def falhar(mensagem: str) -> None:
    print(f"\n[consus] {mensagem}", file=sys.stderr)
    sys.exit(1)


def conferir_ambiente() -> None:
    if sys.version_info < VERSAO_MINIMA:
        atual = ".".join(map(str, sys.version_info[:3]))
        falhar(f"Python {atual} encontrado; o Consus precisa do Python 3.11 ou mais novo.")
    try:
        import django  # noqa: F401
    except ImportError:
        comando = "py -m pip" if os.name == "nt" else f"{Path(sys.executable).name} -m pip"
        falhar(
            "Django não está instalado neste Python.\n"
            f"  Rode: {comando} install -r requirements.txt\n"
            "  (de preferência dentro de um ambiente virtual: python -m venv .venv)"
        )


def _ambiente() -> dict[str, str]:
    """Inclui a pasta do projeto no PYTHONPATH: `config` é importável em qualquer modo do Python."""
    ambiente = dict(os.environ)
    caminhos = [str(RAIZ), *filter(None, ambiente.get("PYTHONPATH", "").split(os.pathsep))]
    ambiente["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(caminhos))
    return ambiente


def manage(*argumentos: str) -> None:
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "manage.py"), *argumentos],
        cwd=RAIZ,
        env=_ambiente(),
        check=False,
    )
    if resultado.returncode != 0:
        falhar(f"'manage.py {' '.join(argumentos)}' falhou (código {resultado.returncode}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicia o Consus sem Docker.")
    parser.add_argument("--porta", default="8000")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--sem-demo", action="store_true", help="não criar dados de demonstração")
    opcoes = parser.parse_args()

    conferir_ambiente()
    os.environ.setdefault("DJANGO_DEBUG", "true")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if "DATABASE_URL" not in os.environ:
        print(f"[consus] Banco: SQLite em {RAIZ / 'db.sqlite3'}")
    else:
        print("[consus] Banco: DATABASE_URL do ambiente")

    usuario = os.environ.setdefault("CONSUS_USUARIO", "admin")
    senha = os.environ.setdefault("CONSUS_SENHA", "consus")

    print("[consus] Aplicando migrações…")
    manage("migrate", "--noinput")
    if not opcoes.sem_demo and not MARCA_DEMO.exists():
        print("[consus] Criando dados de demonstração…")
        manage("popular_demo")
        MARCA_DEMO.write_text("ok\n", encoding="utf-8")
    manage("garantir_usuario")

    endereco = f"http://{'127.0.0.1' if opcoes.host == '0.0.0.0' else opcoes.host}:{opcoes.porta}/"
    print(
        "\n[consus] Pronto!"
        f"\n  Abra {endereco}"
        f"\n  Usuário: {usuario}"
        f"\n  Senha:   {senha}   (troque em Conta → Trocar senha)"
        "\n  Ctrl+C encerra o servidor.\n"
    )
    try:
        subprocess.run(
            [sys.executable, str(RAIZ / "manage.py"), "runserver", f"{opcoes.host}:{opcoes.porta}"],
            cwd=RAIZ,
            env=_ambiente(),
            check=False,
        )
    except KeyboardInterrupt:
        print("\n[consus] Servidor encerrado.")


if __name__ == "__main__":
    main()
