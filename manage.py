#!/usr/bin/env python
"""Utilitário de linha de comando do Django para o Consus."""

import os
import sys
from pathlib import Path

# Garante que `config` e `apps` sejam importáveis mesmo fora da pasta do projeto ou com o
# Python em modo "caminho seguro" (PYTHONSAFEPATH, -P, -I), que não inclui a pasta do script.
RAIZ = str(Path(__file__).resolve().parent)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
