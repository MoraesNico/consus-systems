"""Formulários de movimentação e de filtros (FR-005–FR-007, FR-012, FR-023, FR-026)."""

import datetime

import pytest

from apps.movimentacoes.forms import FiltroMovimentacoesForm, MovimentacaoForm

pytestmark = pytest.mark.django_db

NAO_INTEIRO = "Informe um número inteiro, sem casas decimais nem separadores."


def dados(produto, **extra):
    return {"produto": str(produto.pk), "tipo": "ENTRADA", "quantidade": "5", **extra}


@pytest.mark.parametrize("texto", ["+5", "2,5", "2.5", "1.000", "1e3", "abc"])
def test_fr005_quantidade_so_digitos(produto_com_saldo, texto):
    """FR-005: sinais, decimais e separadores são recusados."""
    form = MovimentacaoForm(data=dados(produto_com_saldo(), quantidade=texto))
    assert form.errors["quantidade"] == [NAO_INTEIRO]


@pytest.mark.parametrize(("texto", "valor"), [(" 7 ", 7), ("007", 7)])
def test_fr005_quantidade_aceita(produto_com_saldo, texto, valor):
    """FR-005: dígitos com espaços nas pontas e zeros à esquerda são aceitos."""
    form = MovimentacaoForm(data=dados(produto_com_saldo(), quantidade=texto))
    assert form.is_valid(), form.errors
    assert form.cleaned_data["quantidade"] == valor


@pytest.mark.parametrize(
    ("texto", "mensagem"),
    [("0", "Informe uma quantidade maior que zero."),
     ("-3", "Informe uma quantidade maior que zero."),
     ("1000001", "Informe no máximo 1.000.000."),
     ("", "Informe a quantidade."), ("  ", "Informe a quantidade.")],
)  # fmt: skip
def test_fr005_limites(produto_com_saldo, texto, mensagem):
    """FR-005: entre 1 e 1.000.000, obrigatória."""
    form = MovimentacaoForm(data=dados(produto_com_saldo(), quantidade=texto))
    assert form.errors["quantidade"] == [mensagem]


def test_fr005_widget_numerico(produto_com_saldo):
    """FR-005: campo texto com teclado numérico, como na 002."""
    html = str(MovimentacaoForm()["quantidade"])
    assert 'type="text"' in html and 'inputmode="numeric"' in html and 'pattern="[0-9]*"' in html


def test_fr007_tipo_so_entrada_ou_saida(produto_com_saldo):
    """FR-007: o formulário não oferece nem aceita "Saldo inicial"."""
    produto = produto_com_saldo()
    assert MovimentacaoForm(data=dados(produto, tipo="INICIAL")).errors["tipo"]
    assert [v for v, _ in MovimentacaoForm().fields["tipo"].choices] == ["ENTRADA", "SAIDA"]


def test_fr007_fr012_produto_valido_e_rotulos(produto_com_saldo):
    """FR-007/FR-012: produto inexistente recusado; opções por nome com "#0001 — Nome"."""
    b = produto_com_saldo(nome="Bucha")
    a = produto_com_saldo(nome="Arruela")
    form = MovimentacaoForm(data={"produto": "99999", "tipo": "ENTRADA", "quantidade": "1"})
    assert form.errors["produto"] == ["Selecione um produto válido."]
    rotulos = [rotulo for valor, rotulo in MovimentacaoForm().fields["produto"].choices if valor]
    assert rotulos == [f"{a.codigo} — Arruela", f"{b.codigo} — Bucha"]


def test_fr006_observacao_longa(produto_com_saldo):
    """FR-006: observação com mais de 200 caracteres é recusada."""
    form = MovimentacaoForm(data=dados(produto_com_saldo(), observacao="x" * 201))
    assert "observacao" in form.errors


def test_fr004_saida_acima_do_saldo_no_formulario(produto_com_saldo):
    """FR-004: o formulário já avisa saldo insuficiente (o serviço confirma sob bloqueio)."""
    form = MovimentacaoForm(data=dados(produto_com_saldo(saldo=10), tipo="SAIDA", quantidade="12"))
    assert form.errors["quantidade"] == ["Saldo insuficiente: disponível 10, solicitado 12"]


def test_fr023_filtro_aceita_dois_formatos_de_data(produto_com_saldo):
    """FR-023: datas em aaaa-mm-dd e dd/mm/aaaa."""
    for de, ate in (("2026-10-01", "2026-10-20"), ("01/10/2026", "20/10/2026")):
        filtros, avisos = FiltroMovimentacoesForm(data={"de": de, "ate": ate}).filtros_validos()
        assert filtros == {"de": datetime.date(2026, 10, 1), "ate": datetime.date(2026, 10, 20)}
        assert avisos == []


def test_fr026_filtros_invalidos_viram_aviso(produto_com_saldo):
    """FR-026: filtros inválidos geram aviso e são ignorados; os válidos continuam."""
    produto = produto_com_saldo()
    form = FiltroMovimentacoesForm(
        data={"produto": str(produto.pk), "tipo": "TROCA", "de": "2026-13-40", "ate": ""}
    )
    filtros, avisos = form.filtros_validos()
    assert filtros == {"produto_id": produto.pk}
    assert "Tipo de movimentação inválido." in avisos and "Data inicial inválida." in avisos
    _, avisos = FiltroMovimentacoesForm(
        data={"de": "2026-10-20", "ate": "2026-10-01"}
    ).filtros_validos()
    assert avisos == ["A data final deve ser igual ou posterior à inicial."]
    _, avisos = FiltroMovimentacoesForm(data={"produto": "99999"}).filtros_validos()
    assert avisos == ["Produto não encontrado."]
