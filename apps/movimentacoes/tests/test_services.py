"""Serviço registrar_movimentacao: soma, subtração, bloqueio de negativo e atomicidade.

FR-001 a FR-008, FR-011 (item 2 da atividade).
"""

import pytest

from apps.movimentacoes import services
from apps.movimentacoes.models import Movimentacao
from apps.movimentacoes.services import (
    EstoqueInsuficienteError,
    MovimentacaoError,
    MovimentacaoInvalidaError,
    SaldoMaximoExcedidoError,
    registrar_movimentacao,
)
from apps.produtos.models import QUANTIDADE_MAXIMA, Produto

pytestmark = pytest.mark.django_db


def registrar(produto, tipo, quantidade, observacao=""):
    return registrar_movimentacao(
        produto_id=produto.pk, tipo=tipo, quantidade=quantidade, observacao=observacao
    )


def saldo(produto) -> int:
    return Produto.objects.get(pk=produto.pk).quantidade_atual


def test_fr002_entrada_soma(produto_com_saldo):
    """FR-002: Entrada soma ao estoque atual."""
    produto = produto_com_saldo(saldo=10)
    mov = registrar(produto, "ENTRADA", 5)
    assert (mov.saldo_anterior, mov.saldo_posterior) == (10, 15)
    assert saldo(produto) == 15


def test_fr003_saida_subtrai(produto_com_saldo):
    """FR-003: Saída/Venda subtrai do estoque atual."""
    produto = produto_com_saldo(saldo=15)
    mov = registrar(produto, "SAIDA", 4, "NF 123")
    assert (mov.saldo_anterior, mov.saldo_posterior, mov.observacao) == (15, 11, "NF 123")
    assert saldo(produto) == 11


def test_fr004_saida_igual_ao_saldo_zera(produto_com_saldo):
    """FR-004: Saída igual ao saldo é permitida e zera o estoque."""
    produto = produto_com_saldo(saldo=11)
    registrar(produto, "SAIDA", 11)
    assert saldo(produto) == 0


def test_fr004_sc002_saida_maior_que_saldo_bloqueada(produto_com_saldo):
    """FR-004/SC-002: o estoque nunca fica negativo; nada é gravado."""
    produto = produto_com_saldo(saldo=3)
    with pytest.raises(EstoqueInsuficienteError) as erro:
        registrar(produto, "SAIDA", 5)
    assert str(erro.value) == "Saldo insuficiente: disponível 3, solicitado 5"
    assert (erro.value.disponivel, erro.value.solicitado) == (3, 5)
    assert isinstance(erro.value, MovimentacaoError)
    assert saldo(produto) == 3
    assert produto.movimentacoes.count() == 1  # só o INICIAL


def test_fr004_mensagem_com_separador_de_milhar(produto_com_saldo):
    """FR-004: números da mensagem usam ponto de milhar."""
    produto = produto_com_saldo(saldo=1200)
    with pytest.raises(EstoqueInsuficienteError, match="disponível 1.200, solicitado 1.500"):
        registrar(produto, "SAIDA", 1500)


@pytest.mark.parametrize("quantidade", [0, -1, 1_000_001, True, 2.5, "3"])
def test_fr005_quantidade_invalida(produto_com_saldo, quantidade):
    """FR-005: quantidade inteira entre 1 e 1.000.000."""
    produto = produto_com_saldo(saldo=10)
    with pytest.raises(MovimentacaoInvalidaError):
        registrar(produto, "ENTRADA", quantidade)
    assert saldo(produto) == 10


def test_fr005_saldo_maximo(produto_com_saldo):
    """FR-005: Entrada que ultrapassaria o teto de saldo é recusada."""
    produto = produto_com_saldo(saldo=QUANTIDADE_MAXIMA - 10)
    with pytest.raises(SaldoMaximoExcedidoError) as erro:
        registrar(produto, "ENTRADA", 11)
    assert "máximo 2.147.483.647" in str(erro.value)
    assert saldo(produto) == QUANTIDADE_MAXIMA - 10


def test_fr006_observacao_aparada_e_limitada(produto_com_saldo):
    """FR-006: observação aparada e com no máximo 200 caracteres."""
    produto = produto_com_saldo()
    assert registrar(produto, "ENTRADA", 1, "  NF 9  ").observacao == "NF 9"
    with pytest.raises(MovimentacaoInvalidaError, match="200 caracteres"):
        registrar(produto, "ENTRADA", 1, "x" * 201)


def test_fr007_tipo_e_produto_invalidos(produto_com_saldo):
    """FR-007: tipo desconhecido e produto inexistente são recusados."""
    produto = produto_com_saldo()
    with pytest.raises(MovimentacaoInvalidaError, match="Tipo de movimentação inválido"):
        registrar(produto, "TROCA", 1)
    with pytest.raises(MovimentacaoInvalidaError, match="não encontrado"):
        registrar_movimentacao(produto_id=99999, tipo="ENTRADA", quantidade=1)


def test_fr008_decide_com_saldo_relido_sob_bloqueio(produto_com_saldo):
    """FR-008: uma instância desatualizada não engana o serviço."""
    produto = produto_com_saldo(saldo=10)
    desatualizado = Produto.objects.get(pk=produto.pk)
    registrar(produto, "SAIDA", 8)
    with pytest.raises(EstoqueInsuficienteError, match="disponível 2, solicitado 5"):
        registrar(desatualizado, "SAIDA", 5)


def test_fr011_falha_na_gravacao_desfaz_o_saldo(produto_com_saldo, monkeypatch):
    """FR-011: se a movimentação não for gravada, o saldo volta (transação)."""
    produto = produto_com_saldo(saldo=10)

    def falhar(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(Movimentacao.objects, "create", falhar)
    with pytest.raises(RuntimeError):
        registrar(produto, "ENTRADA", 5)
    assert saldo(produto) == 10


def test_fr001_edicao_do_produto_nao_altera_saldo(client, produto_com_saldo):
    """FR-001: o saldo não muda pela edição do produto (só por movimentação)."""
    produto = produto_com_saldo(saldo=10)
    client.post(
        f"/produtos/{produto.pk}/editar/",
        {"nome": produto.nome, "estoque_minimo": "3", "quantidade_atual": "999"},
    )
    assert saldo(produto) == 10


def test_fr001_formatar_numero():
    """Mensagens usam o separador de milhar do Consus."""
    assert services.formatar_numero(2_147_483_647) == "2.147.483.647"
