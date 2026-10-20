"""Comando `checar_contraste` (FR-024)."""

from io import StringIO

import pytest
from django.core.management import call_command

from apps.core import design_tokens


def test_fr024_comando_lista_os_pares():
    """FR-024: imprime uma linha por par com a razão e termina sem erro."""
    saida = StringIO()
    call_command("checar_contraste", stdout=saida)
    texto = saida.getvalue()
    assert texto.count(":1") >= len(design_tokens.PARES_CONTRASTE)
    assert "16.13:1" in texto
    assert "31 pares" in texto


def test_fr024_comando_falha_com_par_reprovado(monkeypatch):
    """FR-024: um par reprovado faz o comando terminar com código 1."""
    reprovado = (design_tokens.ParContraste("--color-ink-subtle", "--color-muted-strong", 4.5,
                                            "Par proibido"),)  # fmt: skip
    monkeypatch.setattr(design_tokens, "PARES_CONTRASTE", reprovado)
    with pytest.raises(SystemExit) as erro:
        call_command("checar_contraste", stdout=StringIO())
    assert erro.value.code == 1
