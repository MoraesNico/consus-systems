"""Dinheiro (contrato v1.2): interpretação, formatação e campo em centavos."""

from decimal import Decimal

import pytest
from django.template import Context, Template

from apps.core.dinheiro import (
    CampoDinheiro,
    DinheiroField,
    formatar_csv,
    formatar_moeda,
    interpretar_valor,
)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("12,50", "12.50"), ("1.234,56", "1234.56"), ("R$ 1.234,56", "1234.56"), ("1234", "1234.00"),
     ("12.5", "12.50"), (" 0,99 ", "0.99"), ("R$7", "7.00")],
)  # fmt: skip
def test_interpretar_valor_aceita_formatos_brasileiros(texto, esperado):
    assert interpretar_valor(texto) == Decimal(esperado)


@pytest.mark.parametrize("texto", ["", "-1", "abc", "1,234", "12,5,0", "1.2345", "1e3", None])
def test_interpretar_valor_recusa(texto):
    with pytest.raises(ValueError):
        interpretar_valor(texto)


def test_formatar_moeda():
    assert formatar_moeda(Decimal("1234.5")) == "R$ 1.234,50"
    assert formatar_moeda(Decimal("-3718")) == "−R$ 3.718,00"
    assert formatar_moeda(Decimal("12"), sinal=True) == "+R$ 12,00"
    assert formatar_moeda(Decimal("0"), sinal=True) == "R$ 0,00"
    assert formatar_moeda(None) == "—"
    assert formatar_csv(Decimal("1234.5")) == "1234,50"
    assert formatar_csv(None) == ""


def test_filtro_moeda_no_template():
    html = Template('{{ v|moeda }} {{ v|moeda:"sinal" }}').render(Context({"v": Decimal("5")}))
    assert html == "R$ 5,00 +R$ 5,00"


def test_dinheiro_field_grava_centavos():
    campo = DinheiroField()
    assert campo.get_prep_value(Decimal("12.34")) == 1234
    assert campo.get_prep_value(None) is None
    assert campo.from_db_value(1234, None, None) == Decimal("12.34")
    assert campo.from_db_value(None, None, None) is None
    assert campo.to_python("1.5") == Decimal("1.50")
    with pytest.raises(ValueError):
        campo.get_prep_value(Decimal("0.001"))


def test_campo_dinheiro_formulario():
    campo = CampoDinheiro(required=False)
    assert campo.clean("1.234,56") == Decimal("1234.56")
    assert campo.clean("") is None
    assert campo.prepare_value(Decimal("3.5")) == "3,50"
    with pytest.raises(Exception, match="Informe um valor em reais"):
        campo.clean("doze")
