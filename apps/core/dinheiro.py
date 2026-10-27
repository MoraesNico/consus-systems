"""Dinheiro do Consus (docs/arquitetura.md, "Decisões da Parte 2").

Valores são `Decimal` com 2 casas; no banco, centavos inteiros (`bigint`). `float` é proibido.
"""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")
PRECO_MAXIMO = Decimal("999999.99")

_SO_DIGITOS = re.compile(r"^[0-9]+$")
_MILHAR_BR = re.compile(r"^[0-9]{1,3}(\.[0-9]{3})+(,[0-9]{1,2})?$")
_DECIMAL_BR = re.compile(r"^[0-9]+,[0-9]{1,2}$")
_DECIMAL_PONTO = re.compile(r"^[0-9]+\.[0-9]{1,2}$")

MENSAGEM_VALOR_INVALIDO = "Informe um valor em reais, como 12,50."


def para_centavos(valor: Decimal) -> int:
    return int((Decimal(valor) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def de_centavos(centavos) -> Decimal:
    return (Decimal(int(centavos)) / 100).quantize(CENTAVO)


def interpretar_valor(texto) -> Decimal:
    """Converte `12,50`, `1.234,56`, `R$ 1.234,56`, `1234` ou `12.5` em `Decimal`.

    Recusa negativos, letras e mais de 2 casas (`ValueError`).
    """
    bruto = str(texto or "").strip()
    if bruto.upper().startswith("R$"):
        bruto = bruto[2:].strip()
    bruto = bruto.replace(" ", "")
    if _SO_DIGITOS.match(bruto):
        normalizado = bruto
    elif _MILHAR_BR.match(bruto):
        normalizado = bruto.replace(".", "").replace(",", ".")
    elif _DECIMAL_BR.match(bruto):
        normalizado = bruto.replace(",", ".")
    elif _DECIMAL_PONTO.match(bruto):
        normalizado = bruto
    else:
        raise ValueError(MENSAGEM_VALOR_INVALIDO)
    try:
        return Decimal(normalizado).quantize(CENTAVO)
    except InvalidOperation as erro:  # pragma: no cover - regex já garante dígitos
        raise ValueError(MENSAGEM_VALOR_INVALIDO) from erro


def formatar_moeda(valor, *, sinal: bool = False) -> str:
    """`R$ 1.234,56`; negativo `−R$ 1.234,56` (U+2212); `sinal=True` → `+R$ 12,00`."""
    if valor is None or valor == "":
        return "—"
    numero = Decimal(valor).quantize(CENTAVO)
    inteiro, centavos = f"{abs(numero):.2f}".split(".")
    grupos = f"{int(inteiro):,}".replace(",", ".")
    texto = f"R$ {grupos},{centavos}"
    if numero < 0:
        return f"−{texto}"
    if sinal and numero > 0:
        return f"+{texto}"
    return texto


def formatar_csv(valor) -> str:
    """Dinheiro no CSV: `1234,56` (sem milhar e sem `R$`)."""
    if valor is None:
        return ""
    return f"{Decimal(valor).quantize(CENTAVO):.2f}".replace(".", ",")


class DinheiroField(models.BigIntegerField):
    """Grava centavos inteiros; devolve `Decimal` em reais."""

    description = "Valor em reais (centavos inteiros no banco)"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return de_centavos(value)

    def to_python(self, value):
        if value is None or isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value)).quantize(CENTAVO)
        except InvalidOperation as erro:
            raise ValidationError(MENSAGEM_VALOR_INVALIDO) from erro

    def get_prep_value(self, value):
        if value is None:
            return None
        numero = Decimal(str(value)) if not isinstance(value, Decimal) else value
        if numero != numero.quantize(CENTAVO):
            raise ValueError("Valores monetários têm no máximo 2 casas decimais.")
        return para_centavos(numero)


class CampoDinheiro(forms.Field):
    """Campo de formulário que aceita o formato brasileiro (`1.234,56`)."""

    widget = forms.TextInput(
        attrs={"inputmode": "decimal", "autocomplete": "off", "placeholder": "0,00"}
    )

    def to_python(self, value):
        texto = (value or "").strip() if isinstance(value, str) else value
        if texto in (None, ""):
            return None
        if isinstance(texto, Decimal):
            return texto
        try:
            return interpretar_valor(texto)
        except ValueError as erro:
            raise forms.ValidationError(MENSAGEM_VALOR_INVALIDO, code="valor_invalido") from erro

    def prepare_value(self, value):
        if isinstance(value, Decimal):
            return formatar_csv(value)
        return value
