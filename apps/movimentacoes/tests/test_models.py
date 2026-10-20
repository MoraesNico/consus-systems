"""Modelo Movimentacao: tipos, restrições, apresentação e imutabilidade (FR-009, 010, 016, 021)."""

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.movimentacoes.models import Movimentacao, MovimentacaoImutavelError, TipoMovimentacao

pytestmark = pytest.mark.django_db


def gravar(produto, **campos):
    dados = {"tipo": "ENTRADA", "quantidade": 5, "saldo_anterior": 10, "saldo_posterior": 15}
    dados.update(campos)
    return Movimentacao.objects.create(produto=produto, **dados)


def test_tipos_e_rotulos():
    """FR-016: tipos INICIAL, ENTRADA e SAIDA com rótulos em pt-BR."""
    assert dict(TipoMovimentacao.choices) == {
        "INICIAL": "Saldo inicial",
        "ENTRADA": "Entrada",
        "SAIDA": "Saída/Venda",
    }


@pytest.mark.parametrize(
    "campos",
    [
        {"tipo": "OUTRO"},
        {"tipo": "ENTRADA", "quantidade": 0, "saldo_posterior": 10},
        {"tipo": "ENTRADA", "saldo_posterior": 99},
        {"tipo": "SAIDA", "quantidade": 5, "saldo_anterior": 10, "saldo_posterior": 15},
        {"tipo": "INICIAL", "quantidade": 5, "saldo_anterior": 10, "saldo_posterior": 15},
    ],
)
def test_fr009_fr010_restricoes_do_banco(produto_com_saldo, campos):
    """FR-009/FR-010: o banco recusa tipo inválido, quantidade 0 e saldos incoerentes."""
    produto = produto_com_saldo()
    with pytest.raises(IntegrityError), transaction.atomic():
        gravar(produto, **campos)


def test_fr010_inicial_unico_por_produto(produto_com_saldo):
    """FR-010: no máximo um INICIAL por produto (o cadastro já criou um)."""
    produto = produto_com_saldo(saldo=0)
    with pytest.raises(IntegrityError), transaction.atomic():
        gravar(produto, tipo="INICIAL", quantidade=0, saldo_anterior=0, saldo_posterior=0)


def test_fr009_saldo_negativo_recusado(produto_com_saldo):
    """FR-009: saldo posterior negativo é impossível no banco."""
    produto = produto_com_saldo()
    with pytest.raises(IntegrityError), transaction.atomic():
        gravar(produto, tipo="SAIDA", quantidade=15, saldo_anterior=10, saldo_posterior=-5)


def test_ordenacao_padrao_mais_recente_primeiro(produto_com_saldo):
    """A ordenação padrão é -criado_em, -id."""
    produto = produto_com_saldo()
    nova = gravar(produto)
    assert Movimentacao.objects.filter(produto=produto).first() == nova


def test_fr016_apresentacao(produto_com_saldo):
    """FR-016: sinal tipográfico, quantidade assinada, selo e mensagem de confirmação."""
    produto = produto_com_saldo(nome="Parafuso", saldo=10)
    saida = gravar(produto, tipo="SAIDA", quantidade=3, saldo_anterior=10, saldo_posterior=7)
    entrada = Movimentacao(produto=produto, tipo="ENTRADA", quantidade=5, saldo_anterior=10,
                           saldo_posterior=15)  # fmt: skip
    inicial = produto.movimentacoes.get(tipo="INICIAL")
    assert (saida.sinal, saida.quantidade_assinada) == ("−", -3)
    assert (entrada.sinal, entrada.quantidade_assinada) == ("+", 5)
    assert (entrada.variante_selo, entrada.icone_selo) == ("info", "arrow-down-to-line")
    assert (saida.variante_selo, saida.icone_selo) == ("neutro", "arrow-up-from-line")
    assert (inicial.variante_selo, inicial.icone_selo) == ("neutro", "")
    assert (
        saida.mensagem_confirmacao == f"Saída registrada: {produto.codigo} Parafuso — saldo 10 → 7"
    )
    assert entrada.mensagem_confirmacao.startswith("Entrada registrada:")
    assert inicial.mensagem_confirmacao.startswith("Saldo inicial registrado:")


def test_fr016_mensagem_limitada_a_200_caracteres(produto_com_saldo):
    """FR-016: a mensagem cabe no toast (≤ 200) mesmo com nome de 120 caracteres."""
    produto = produto_com_saldo(nome="N" * 120, saldo=1_000_000_000)
    mov = Movimentacao(produto=produto, tipo="ENTRADA", quantidade=1_000_000,
                       saldo_anterior=1_000_000_000, saldo_posterior=1_001_000_000)  # fmt: skip
    assert len(mov.mensagem_confirmacao) <= 200
    assert produto.codigo in mov.mensagem_confirmacao


def test_fr021_movimentacoes_sao_imutaveis(produto_com_saldo):
    """FR-021: save/delete de registro existente e update/delete em massa são proibidos."""
    produto = produto_com_saldo()
    mov = produto.movimentacoes.get()
    mov.observacao = "alterada"
    with pytest.raises(MovimentacaoImutavelError):
        mov.save()
    with pytest.raises(MovimentacaoImutavelError):
        mov.delete()
    with pytest.raises(MovimentacaoImutavelError):
        Movimentacao.objects.update(observacao="x")
    with pytest.raises(MovimentacaoImutavelError):
        Movimentacao.objects.all().delete()


def test_fr021_produto_com_historico_protegido(produto_com_saldo):
    """FR-021: produto com movimentações não pode ser apagado."""
    produto = produto_com_saldo()
    with pytest.raises(ProtectedError):
        produto.delete()
