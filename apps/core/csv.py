"""CSV do Consus (004, 008): `;`, CRLF, BOM opcional e proteção contra injeção de fórmula."""

import csv
import io
from collections.abc import Iterable, Sequence

_PREFIXOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def proteger_celula(texto: str) -> str:
    """Proteção contra injeção de fórmula em planilhas (OWASP "CSV Injection")."""
    return f"'{texto}" if texto.startswith(_PREFIXOS_FORMULA) else texto


def montar_csv(cabecalho: Sequence[str], linhas: Iterable[Sequence], *, bom: bool) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return ("﻿" if bom else "") + saida.getvalue()
