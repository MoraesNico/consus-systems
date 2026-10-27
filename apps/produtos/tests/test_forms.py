"""Formulários de produto: inteiros estritos e mensagens pt-BR (FR-004, 006, 007, 025)."""

import pytest

from apps.produtos.forms import ProdutoEdicaoForm, ProdutoForm

INVALIDO = "Informe um número inteiro igual ou maior que zero."


def dados(**kwargs) -> dict:
    return {"nome": "Caneta", "quantidade_inicial": "1", "estoque_minimo": "1",
            "preco_custo": "1,00", "preco_venda": "2,00", **kwargs}  # fmt: skip


@pytest.mark.parametrize(("texto", "esperado"), [("0", 0), ("7", 7), (" 12 ", 12), ("007", 7)])
def test_fr006_inteiro_estrito_aceita(texto, esperado):
    """FR-006: só dígitos (com espaços nas pontas) são aceitos."""
    form = ProdutoForm(data=dados(quantidade_inicial=texto))
    assert form.is_valid(), form.errors
    assert form.cleaned_data["quantidade_inicial"] == esperado


@pytest.mark.parametrize(
    "texto", ["-5", "2,5", "2.5", "2.0", "1.000", "1e3", "+5", "dez", "٣", "²"]
)
def test_fr006_inteiro_estrito_recusa(texto):
    """FR-006: sinais, decimais, separador de milhar, notação científica e Unicode são recusados."""
    form = ProdutoForm(data=dados(quantidade_inicial=texto, estoque_minimo=texto))
    assert not form.is_valid()
    assert form.errors["quantidade_inicial"] == [INVALIDO]
    assert form.errors["estoque_minimo"] == [INVALIDO]


def test_fr006_acima_do_maximo():
    """FR-006: acima de 2.147.483.647 → mensagem com o limite formatado."""
    form = ProdutoForm(data=dados(quantidade_inicial="2147483648"))
    assert form.errors["quantidade_inicial"] == ["Informe um valor de no máximo 2.147.483.647."]


def test_fr006_campos_numericos_obrigatorios_sem_valor_inicial():
    """FR-006: quantidade e mínimo são obrigatórios e começam vazios."""
    form = ProdutoForm(data={"nome": "Caneta"})
    assert form.errors["quantidade_inicial"] == ["Informe a quantidade inicial."]
    assert form.errors["estoque_minimo"] == ["Informe o estoque mínimo."]
    vazio = ProdutoForm()
    assert vazio["quantidade_inicial"].value() is None
    assert vazio["estoque_minimo"].value() is None


def test_fr007_mensagens_nome_ptbr():
    """FR-007: mensagens do nome em pt-BR."""
    assert ProdutoForm(data=dados(nome="  ")).errors["nome"] == ["Informe o nome do produto."]
    longo = ProdutoForm(data=dados(nome="x" * 121))
    assert longo.errors["nome"] == ["O nome deve ter no máximo 120 caracteres."]


def test_fr004_form_normaliza_nome():
    """FR-004: o formulário entrega o nome normalizado."""
    form = ProdutoForm(data=dados(nome="  Caneta    Azul "))
    assert form.is_valid() and form.cleaned_data["nome"] == "Caneta Azul"


def test_fr006_widget_numerico_texto():
    """FR-006: campo numérico é texto com teclado numérico e padrão de dígitos."""
    html = str(ProdutoForm()["quantidade_inicial"])
    assert 'type="text"' in html and 'inputmode="numeric"' in html and 'pattern="[0-9]*"' in html


def test_fr025_form_edicao_so_nome_e_estoque_minimo():
    """FR-025: a edição só expõe nome e estoque mínimo."""
    assert list(ProdutoEdicaoForm().fields) == [
        "nome", "estoque_minimo", "preco_custo", "preco_venda"]  # fmt: skip
